import io
import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.core.mail import EmailMessage, send_mail
from django.conf import settings
from django.contrib import messages

from .models import ExamCategory, Exam, Question, StudentAnswer, ExamResult
import openpyxl

# ----------------- Utility Functions -----------------
def is_admin(user):
    return user.is_staff

# ----------------- Login -----------------
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_staff:
                return redirect('exams:admin_dashboard')
            return redirect('exams:student_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'exams/login.html', {'form': form})

# ----------------- Dashboards -----------------
@login_required
def student_dashboard(request):
    exams = Exam.objects.all()
    results = ExamResult.objects.filter(student=request.user)
    return render(request, 'exams/student_dashboard.html', {'exams': exams, 'results': results})

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    categories = ExamCategory.objects.filter(parent__isnull=True)
    return render(request, 'exams/admin_dashboard.html', {'categories': categories})

# ----------------- Category Detail / Add Question -----------------
@login_required
@user_passes_test(is_admin)
def category_detail(request, category_id):
    category = get_object_or_404(ExamCategory, id=category_id)
    subcategories = ExamCategory.objects.filter(parent=category)
    exams = Exam.objects.filter(category=category)
    questions = Question.objects.filter(exam_category=category)
    question_count = json.loads(category.question_count)

    if request.method == 'POST':
        subject = request.POST.get('subject')
        text = request.POST.get('text')
        question_type = request.POST.get('question_type')
        image = request.FILES.get('image')

        if not all([subject, text, question_type]):
            messages.error(request, 'Subject, text, and question type are required.')
            return render(request, 'exams/category_detail.html', locals())

        if question_type not in ['MCQ_SINGLE', 'MCQ_MULTI', 'NUMERICAL']:
            messages.error(request, 'Invalid question type.')
            return render(request, 'exams/category_detail.html', locals())

        # Check question count limit
        current_counts = {q.subject: questions.filter(subject=q.subject, question_type=question_type).count() for q in questions}
        if isinstance(question_count.get(subject), dict) and question_type in question_count.get(subject, {}):
            if current_counts.get(subject, 0) >= question_count[subject].get(question_type, 0):
                messages.error(request, f'Maximum {question_type} questions for {subject} reached.')
                return render(request, 'exams/category_detail.html', locals())
        elif question_count.get(subject) and questions.filter(subject=subject).count() >= question_count[subject]:
            messages.error(request, f'Maximum questions for {subject} reached.')
            return render(request, 'exams/category_detail.html', locals())

        # Handle options
        option1 = option2 = option3 = option4 = ''
        if question_type in ['MCQ_SINGLE', 'MCQ_MULTI']:
            option1 = request.POST.get('option1')
            option2 = request.POST.get('option2')
            option3 = request.POST.get('option3')
            option4 = request.POST.get('option4')
            if not all([option1, option2, option3, option4]):
                messages.error(request, 'All options are required for MCQs.')
                return render(request, 'exams/category_detail.html', locals())

            if question_type == 'MCQ_SINGLE':
                correct_option = request.POST.get('correct_option')
                if correct_option not in ['option1', 'option2', 'option3', 'option4']:
                    messages.error(request, 'Invalid correct option selected.')
                    return render(request, 'exams/category_detail.html', locals())
            else:  # MCQ_MULTI
                correct_options = request.POST.getlist('correct_options')
                if not correct_options:
                    messages.error(request, 'At least one correct option required for MCQ Multi.')
                    return render(request, 'exams/category_detail.html', locals())
                correct_option = ','.join(sorted(correct_options))
        else:  # NUMERICAL
            correct_option = request.POST.get('correct_value')
            if not correct_option:
                messages.error(request, 'Correct value required for Numerical.')
                return render(request, 'exams/category_detail.html', locals())

        question = Question(
            exam_category=category,
            subject=subject,
            question_type=question_type,
            text=text,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=correct_option,
            image=image
        )
        question.save()
        messages.success(request, 'Question added successfully!')
        return redirect('exams:category_detail', category_id=category.id)

    return render(request, 'exams/category_detail.html', locals())

# ----------------- Take Exam -----------------
@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = Question.objects.filter(exam_category=exam.category)
    duration_minutes = 180
    time_left = duration_minutes * 60

    if request.session.get(f'exam_{exam_id}_start'):
        start_time = timezone.datetime.fromisoformat(request.session[f'exam_{exam_id}_start'])
        elapsed = (timezone.now() - start_time).total_seconds()
        time_left = max(0, duration_minutes * 60 - elapsed)
        if time_left == 0:
            return redirect('exams:submit_exam', exam_id=exam_id)
    else:
        request.session[f'exam_{exam_id}_start'] = timezone.now().isoformat()

    if request.method == 'POST':
        for question in questions:
            selected = ''
            if question.question_type == 'MCQ_MULTI':
                selected_options = request.POST.getlist(f'question_{question.id}')
                selected = ','.join(sorted(selected_options)) if selected_options else ''
            else:
                selected = request.POST.get(f'question_{question.id}', '')
            if selected:
                StudentAnswer.objects.create(
                    student=request.user,
                    exam=exam,
                    question=question,
                    selected_option=selected,
                    is_correct=False
                )
        return redirect('exams:submit_exam', exam_id=exam_id)

    return render(request, 'exams/take_exam.html', {
        'exam': exam,
        'questions': questions,
        'time_left': time_left
    })

# ----------------- Submit Exam -----------------
@login_required
def submit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    answers = StudentAnswer.objects.filter(exam=exam, student=request.user)

    # Default marking schemes (can adjust per exam)
    default_scheme = {
        "MCQ_SINGLE": {"correct": 1, "wrong": 0, "partial": 0},
        "MCQ_MULTI": {"correct": 2, "wrong": 0, "partial": 1},
        "NUMERICAL": {"correct": 1, "wrong": 0, "partial": 0},
    }
    scheme = exam.category.marking_scheme or default_scheme

    marks_obtained = 0
    total_marks = 0
    subject_summary = {}
    wrong_answers = []

    # Compute marks and summary
    for answer in answers:
        q = answer.question
        marks = scheme.get(q.question_type, default_scheme[q.question_type])
        correct_score = marks['correct']
        incorrect_score = marks['wrong']
        partial_score = marks['partial']
        total_marks += correct_score

        subj = q.subject or "General"
        if subj not in subject_summary:
            subject_summary[subj] = {'attempted': 0, 'not_attempted': 0, 'right': 0, 'wrong': 0, 'total_marks': 0}

        subject_summary[subj]['attempted'] += 1
        subject_summary[subj]['total_marks'] += correct_score

        if q.question_type == 'MCQ_MULTI':
            selected = set(answer.selected_option.split(',')) if answer.selected_option else set()
            correct = set(q.correct_option.split(','))
            num_correct = len(selected & correct)

            if num_correct == len(correct) and len(selected) == len(correct):
                answer.is_correct = True
                marks_obtained += correct_score
                subject_summary[subj]['right'] += 1
            elif num_correct > 0:
                answer.is_correct = False
                marks_obtained += partial_score * num_correct
                subject_summary[subj]['wrong'] += 1
                wrong_answers.append(answer)
            else:
                answer.is_correct = False
                marks_obtained += incorrect_score
                subject_summary[subj]['wrong'] += 1
                wrong_answers.append(answer)
        else:
            if answer.selected_option == q.correct_option:
                answer.is_correct = True
                marks_obtained += correct_score
                subject_summary[subj]['right'] += 1
            else:
                answer.is_correct = False
                marks_obtained += incorrect_score
                subject_summary[subj]['wrong'] += 1
                wrong_answers.append(answer)

        answer.save()

    # Count not attempted
    for q in Question.objects.filter(exam_category=exam.category):
        subj = q.subject or "General"
        if subj in subject_summary and not answers.filter(question=q).exists():
            subject_summary[subj]['not_attempted'] += 1

    # Save result
    ExamResult.objects.filter(student=request.user, exam=exam).delete()
    ExamResult.objects.create(
        student=request.user,
        exam=exam,
        marks_obtained=marks_obtained,
        total_marks=total_marks
    )

    request.session.pop(f'exam_{exam_id}_start', None)

    # Return result to template
    return render(request, 'exams/exam_result.html', {
        'exam': exam,
        'subject_summary': subject_summary,
        'wrong_answers': wrong_answers,
        'marks_obtained': marks_obtained,
        'total_marks': total_marks,
        'marking_scheme': scheme
    })
