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
from .email_utils import send_exam_report_email
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

        # Handle question options
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
# ----------------- Submit Exam -----------------
@login_required
def submit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    all_questions = Question.objects.filter(exam_category=exam.category)

    # Save all submitted answers first
    if request.method == 'POST':
        for question in all_questions:
            selected = ''
            if question.question_type == 'MCQ_MULTI':
                selected_options = request.POST.getlist(f'question_{question.id}')
                selected = ','.join(sorted(selected_options)) if selected_options else ''
            else:
                selected = request.POST.get(f'question_{question.id}', '')
            StudentAnswer.objects.update_or_create(
                student=request.user,
                exam=exam,
                question=question,
                defaults={'selected_option': selected, 'is_correct': False}
            )

    # Evaluate answers
    answers = StudentAnswer.objects.filter(exam=exam, student=request.user)
    default_scheme = {
        "MCQ_SINGLE": {"correct": 1, "wrong": 0, "partial": 0},
        "MCQ_MULTI": {"correct": 2, "wrong": 0, "partial": 1},
        "NUMERICAL": {"correct": 1, "wrong": 0, "partial": 0},
    }
    scheme = exam.category.marking_scheme or default_scheme

    total_marks_obtained = 0
    total_marks = 0
    subject_stats = {}
    wrong_questions = []

    # Initialize per-subject stats
    for q in all_questions:
        subj = q.subject or "General"
        if subj not in subject_stats:
            subject_stats[subj] = {
                "attempted": 0,
                "not_attempted": 0,
                "correct": 0,
                "wrong": 0,
                "marks_obtained": 0,
                "total_marks": 0
            }
        subject_stats[subj]["total_marks"] += scheme.get(q.question_type, default_scheme[q.question_type])['correct']

    # Evaluate each answer
    for answer in answers:
        q = answer.question
        subj = q.subject or "General"
        marks = scheme.get(q.question_type, default_scheme[q.question_type])
        correct_score = marks['correct']
        incorrect_score = marks['wrong']
        partial_score = marks['partial']

        obtained = 0
        is_correct = False

        if not answer.selected_option:
            subject_stats[subj]["not_attempted"] += 1
        else:
            subject_stats[subj]["attempted"] += 1
            if q.question_type == 'MCQ_MULTI':
                selected = set(answer.selected_option.split(','))
                correct = set(q.correct_option.split(','))
                num_correct = len(selected & correct)

                if num_correct == len(correct) and len(selected) == len(correct):
                    is_correct = True
                    obtained = correct_score
                elif num_correct > 0:
                    is_correct = False
                    obtained = partial_score * num_correct
                else:
                    is_correct = False
                    obtained = incorrect_score
            else:
                if answer.selected_option == q.correct_option:
                    is_correct = True
                    obtained = correct_score
                else:
                    is_correct = False
                    obtained = incorrect_score

            if not is_correct:
                wrong_questions.append({
                    "question": q.text,
                    "student_answer": answer.selected_option,
                    "correct_answer": q.correct_option
                })

            if is_correct:
                subject_stats[subj]["correct"] += 1
            else:
                subject_stats[subj]["wrong"] += 1

        answer.is_correct = is_correct
        answer.save()
        total_marks_obtained += obtained
        total_marks += correct_score
        subject_stats[subj]["marks_obtained"] += obtained

    # Save exam result
    ExamResult.objects.filter(student=request.user, exam=exam).delete()
    ExamResult.objects.create(
        student=request.user,
        exam=exam,
        marks_obtained=total_marks_obtained,
        total_marks=total_marks
    )

    # Remove exam start session
    request.session.pop(f'exam_{exam_id}_start', None)

    # ----------------- Send Email -----------------
    try:
        from .email_utils import send_exam_report_email  # make sure your function is in email_utils.py
        send_exam_report_email(subject_stats, wrong_questions, total_marks_obtained, total_marks)
    except Exception as e:
        messages.error(request, f"Failed to send email: {e}")

    # Render result page
    return render(request, 'exams/exam_result.html', {
        'exam': exam,
        'subject_stats': subject_stats,
        'wrong_questions': wrong_questions,
        'total_marks_obtained': total_marks_obtained,
        'total_marks': total_marks
    })
