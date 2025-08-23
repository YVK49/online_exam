from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.contrib import messages
from .models import ExamCategory, Exam, Question, StudentAnswer, ExamResult
import json
import io
import openpyxl

# -------------------- Helpers --------------------
def is_admin(user):
    return user.is_staff

def get_marking_scheme(exam_type):
    exam_type = exam_type.upper()
    if exam_type == "EAMCET":
        return {"MCQ_SINGLE": 1, "MCQ_MULTI": 2}  # no negative, no numerical
    elif exam_type == "JEE_MAINS":
        return {"MCQ_SINGLE": 4, "MCQ_MULTI": 4, "NUMERICAL": 4}
    elif exam_type == "JEE_ADVANCED":
        return {"MCQ_SINGLE": 3, "MCQ_MULTI": 4, "NUMERICAL": 4}
    return {"MCQ_SINGLE": 1, "MCQ_MULTI": 2, "NUMERICAL": 2}  # default

# -------------------- Auth --------------------
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

# -------------------- Dashboards --------------------
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

# -------------------- Category & Questions --------------------
@login_required
@user_passes_test(is_admin)
def category_detail(request, category_id):
    category = get_object_or_404(ExamCategory, id=category_id)
    subcategories = ExamCategory.objects.filter(parent=category)
    exams = Exam.objects.filter(category=category)
    questions = Question.objects.filter(exam_category=category)
    question_count = json.loads(category.question_count or "{}")

    if request.method == 'POST':
        subject = request.POST.get('subject')
        text = request.POST.get('text')
        question_type = request.POST.get('question_type')
        image = request.FILES.get('image')

        if not all([subject, text, question_type]):
            messages.error(request, 'Subject, text, and question type are required.')
            return redirect('exams:category_detail', category_id=category.id)

        # Option handling
        if question_type in ['MCQ_SINGLE', 'MCQ_MULTI']:
            option1 = request.POST.get('option1')
            option2 = request.POST.get('option2')
            option3 = request.POST.get('option3')
            option4 = request.POST.get('option4')
            if not all([option1, option2, option3, option4]):
                messages.error(request, 'All options are required for MCQ questions.')
                return redirect('exams:category_detail', category_id=category.id)

            if question_type == 'MCQ_SINGLE':
                correct_option = request.POST.get('correct_option')
                if correct_option not in ['option1', 'option2', 'option3', 'option4']:
                    messages.error(request, 'Invalid correct option.')
                    return redirect('exams:category_detail', category_id=category.id)
            else:  # MCQ_MULTI
                correct_options = request.POST.getlist('correct_options')
                if not correct_options:
                    messages.error(request, 'At least one correct option required.')
                    return redirect('exams:category_detail', category_id=category.id)
                correct_option = ','.join(sorted(correct_options))
        else:  # NUMERICAL
            option1 = option2 = option3 = option4 = ''
            correct_option = request.POST.get('correct_value')
            if not correct_option:
                messages.error(request, 'Correct value required for Numerical.')
                return redirect('exams:category_detail', category_id=category.id)

        # Save Question
        Question.objects.create(
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
        messages.success(request, 'Question added successfully!')
        return redirect('exams:category_detail', category_id=category.id)

    return render(request, 'exams/category_detail.html', {
        'category': category, 'subcategories': subcategories, 'exams': exams,
        'questions': questions, 'question_count': question_count
    })

# -------------------- Take Exam --------------------
@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = Question.objects.filter(exam_category=exam.category)

    # Load constraints
    try:
        constraints = json.loads(exam.category.question_count or "{}")
    except:
        constraints = {}

    duration_minutes = constraints.get("duration", 180)
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
        'time_left': time_left,
        'constraints': constraints
    })

# -------------------- Submit Exam & Results --------------------
@login_required
def submit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    answers = StudentAnswer.objects.filter(exam=exam, student=request.user)
    questions = Question.objects.filter(exam_category=exam.category)

    scheme = get_marking_scheme(exam.exam_type)

    subject_summary = {}
    total_marks_obtained = 0
    total_marks_possible = 0
    total_right = 0
    total_wrong = 0
    wrong_answers_list = []

    # Initialize subject summary
    for q in questions:
        subj = q.subject
        if subj not in subject_summary:
            subject_summary[subj] = {"total":0,"attempted":0,"not_attempted":0,"right":0,"wrong":0,"marks_obtained":0}
        subject_summary[subj]["total"] += 1
        total_marks_possible += scheme.get(q.question_type, 1)

    # Evaluate answers
    for answer in answers:
        q = answer.question
        subj = q.subject
        subject_summary[subj]["attempted"] += 1
        correct_marks = scheme.get(q.question_type, 1)

        if q.question_type == "MCQ_MULTI":
            selected = set(answer.selected_option.split(',')) if answer.selected_option else set()
            correct = set(q.correct_option.split(','))
            if selected == correct:
                answer.is_correct = True
                subject_summary[subj]["right"] += 1
                subject_summary[subj]["marks_obtained"] += correct_marks
                total_right += 1
                total_marks_obtained += correct_marks
            else:
                answer.is_correct = False
                subject_summary[subj]["wrong"] += 1
                wrong_answers_list.append(answer)
                total_wrong += 1
        else:
            if answer.selected_option == q.correct_option:
                answer.is_correct = True
                subject_summary[subj]["right"] += 1
                subject_summary[subj]["marks_obtained"] += correct_marks
                total_right += 1
                total_marks_obtained += correct_marks
            else:
                answer.is_correct = False
                subject_summary[subj]["wrong"] += 1
                wrong_answers_list.append(answer)
                total_wrong += 1

        answer.save()

    # Calculate not attempted
    for subj in subject_summary:
        subject_summary[subj]["not_attempted"] = subject_summary[subj]["total"] - subject_summary[subj]["attempted"]

    # Save exam result
    ExamResult.objects.filter(student=request.user, exam=exam).delete()
    ExamResult.objects.create(
        student=request.user,
        exam=exam,
        marks_obtained=total_marks_obtained,
        total_marks=total_marks_possible
    )

    request.session.pop(f'exam_{exam_id}_start', None)

    # Render result
    return render(request, 'exams/exam_result.html', {
        "exam": exam,
        "subject_summary": subject_summary,
        "total_marks_obtained": total_marks_obtained,
        "total_marks_possible": total_marks_possible,
        "total_right": total_right,
        "total_wrong": total_wrong,
        "wrong_answers_list": wrong_answers_list,
        "scheme": scheme
    })
