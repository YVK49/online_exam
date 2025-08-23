from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.core.mail import EmailMessage
from .models import ExamCategory, Exam, Question, StudentAnswer, ExamResult
from django.contrib import messages
import json
from datetime import timedelta
import openpyxl
from django.core.mail import EmailMessage
from django.conf import settings

def get_marks_for_question(question):
    default_scheme = {
        "MCQ_SINGLE": {"correct": 1, "wrong": -0.25},
        "MCQ_MULTI": {"correct": 2, "wrong": -0.5},
        "NUMERICAL": {"correct": 2, "wrong": 0}
    }
    scheme = question.exam.category.marking_scheme or default_scheme
    return scheme.get(question.question_type, default_scheme[question.question_type])

def is_admin(user):
    return user.is_staff

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

        # Validation
        if not all([subject, text, question_type]):
            messages.error(request, 'Subject, text, and question type are required.')
        elif question_type not in ['MCQ_SINGLE', 'MCQ_MULTI', 'NUMERICAL']:
            messages.error(request, 'Invalid question type.')
        else:
            # Check question count limit
            current_counts = {q.subject: questions.filter(subject=q.subject, question_type=question_type).count() for q in questions}
            if isinstance(question_count.get(subject), dict) and question_type in question_count.get(subject, {}):
                if current_counts.get(subject, 0) >= question_count[subject].get(question_type, 0):
                    messages.error(request, f'Maximum {question_type} questions ({question_count[subject][question_type]}) for {subject} reached.')
                    return render(request, 'exams/category_detail.html', {
                        'category': category, 'subcategories': subcategories, 'exams': exams,
                        'questions': questions, 'question_count': question_count
                    })
            elif question_count.get(subject) and questions.filter(subject=subject).count() >= question_count[subject]:
                messages.error(request, f'Maximum questions ({question_count[subject]}) for {subject} reached.')
                return render(request, 'exams/category_detail.html', {
                    'category': category, 'subcategories': subcategories, 'exams': exams,
                    'questions': questions, 'question_count': question_count
                })

            # Handle question types
            if question_type in ['MCQ_SINGLE', 'MCQ_MULTI']:
                option1 = request.POST.get('option1')
                option2 = request.POST.get('option2')
                option3 = request.POST.get('option3')
                option4 = request.POST.get('option4')
                if not all([option1, option2, option3, option4]):
                    messages.error(request, 'All options are required for MCQ questions.')
                    return render(request, 'exams/category_detail.html', {
                        'category': category, 'subcategories': subcategories, 'exams': exams,
                        'questions': questions, 'question_count': question_count
                    })
                if question_type == 'MCQ_SINGLE':
                    correct_option = request.POST.get('correct_option')
                    if correct_option not in ['option1', 'option2', 'option3', 'option4']:
                        messages.error(request, 'Invalid correct option selected.')
                        return render(request, 'exams/category_detail.html', {
                            'category': category, 'subcategories': subcategories, 'exams': exams,
                            'questions': questions, 'question_count': question_count
                        })
                else:  # MCQ_MULTI
                    correct_options = request.POST.getlist('correct_options')
                    if not correct_options:
                        messages.error(request, 'At least one correct option required for MCQ Multi.')
                        return render(request, 'exams/category_detail.html', {
                            'category': category, 'subcategories': subcategories, 'exams': exams,
                            'questions': questions, 'question_count': question_count
                        })
                    correct_option = ','.join(sorted(correct_options))
            else:  # NUMERICAL
                option1 = option2 = option3 = option4 = ''
                correct_option = request.POST.get('correct_value')
                if not correct_option:
                    messages.error(request, 'Correct value required for Numerical.')
                    return render(request, 'exams/category_detail.html', {
                        'category': category, 'subcategories': subcategories, 'exams': exams,
                        'questions': questions, 'question_count': question_count
                    })

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

    return render(request, 'exams/category_detail.html', {
        'category': category, 'subcategories': subcategories, 'exams': exams,
        'questions': questions, 'question_count': question_count
    })

@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = Question.objects.filter(exam_category=exam.category)

    # ✅ Load constraints (time, question counts, etc.) from category
    try:
        constraints = json.loads(exam.category.question_count)
    except Exception:
        constraints = {}

    # ✅ Default duration fallback if not in Excel
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
        'constraints': constraints  # ✅ Pass constraints to template
    })


import openpyxl
from django.core.mail import EmailMessage

@login_required
def submit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    answers = StudentAnswer.objects.filter(exam=exam, student=request.user)

    # ✅ Load marking scheme from DB or use defaults
    type_scheme = exam.category.marking_scheme or {
        'MCQ_SINGLE': (1, 0, 0),
        'NUMERICAL': (1, 0, 0),
    }

    marks_obtained = 0
    total_marks = 0

    for answer in answers:
        q = answer.question
        correct_score, incorrect_score, partial_score = type_scheme.get(q.question_type, (1, 0, 0))
        total_marks += correct_score

        if q.question_type == 'MCQ_MULTI':
            selected = set(answer.selected_option.split(',')) if answer.selected_option else set()
            correct = set(q.correct_option.split(','))
            num_correct = len(selected & correct)

            if num_correct == len(correct) and len(selected) == len(correct):
                answer.is_correct = True
                marks_obtained += correct_score
            elif num_correct > 0:
                answer.is_correct = False
                marks_obtained += partial_score * num_correct
            else:
                answer.is_correct = False
                marks_obtained += incorrect_score
        elif answer.selected_option == q.correct_option:
            answer.is_correct = True
            marks_obtained += correct_score
        else:
            answer.is_correct = False
            marks_obtained += incorrect_score

        answer.save()

    ExamResult.objects.create(
        student=request.user,
        exam=exam,
        marks_obtained=marks_obtained,
        total_marks=total_marks
    )

    request.session.pop(f'exam_{exam_id}_start', None)

    # ✅ Excel report for management
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Exam Results"
    ws.append(["Student", "Exam", "Category", "Marks", "Total", "Date"])

    results = ExamResult.objects.filter(exam=exam)
    for r in results:
        ws.append([
            r.student.username,
            r.exam.title,
            r.exam.category.name,
            r.marks_obtained,
            r.total_marks,
            r.completed_at.strftime("%Y-%m-%d %H:%M"),
        ])

    file_stream = io.BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    email = EmailMessage(
        subject=f"Exam Results Report - {exam.category.name}",
        body="Attached is the latest results report.",
        from_email="noreply@exam.com",
        to=["management@example.com"],
    )
    email.attach(f"{exam.category.name}_results.xlsx", file_stream.getvalue(), "application/vnd.ms-excel")
    email.send(fail_silently=True)

    return render(request, 'exams/exam_result.html', {
        'exam': exam,
        'answers': answers,
        'marks_obtained': marks_obtained,
        'total_marks': total_marks
    })

    # -----------------------------
    # Email result to college
    # -----------------------------
    from django.core.mail import send_mail
    from django.conf import settings

    subject = f"Exam Result: {exam.title} - {request.user.username}"
    message = (
        f"Student: {request.user.username}\n"
        f"Exam: {exam.title}\n"
        f"Marks Obtained: {marks_obtained}/{total_marks}\n\n"
        f"Submitted on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # 🔹 College management fixed email
    recipient_list = ["tilluvissu@gmail.com"]

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
    except Exception as e:
        print("Error sending email:", e)

    return render(request, 'exams/exam_result.html', {
        'exam': exam,
        'answers': answers,
        'marks_obtained': marks_obtained,
        'total_marks': total_marks
    })
