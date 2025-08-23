from django.db import models
from django.contrib.auth.models import User

class ExamCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    question_count = models.JSONField()  # e.g., {"Physics": {"MCQ_SINGLE": 20, "NUMERICAL": 5}}
    marking_scheme = models.JSONField(default=dict, blank=True)  # ✅ Advanced marking scheme

    def __str__(self):
        return self.name


class Question(models.Model):
    QUESTION_TYPES = [
        ('MCQ_SINGLE', 'Single Choice'),
        ('MCQ_MULTI', 'Multiple Choice'),
        ('NUMERICAL', 'Numerical'),
    ]

    subject = models.CharField(max_length=100)
    question_type = models.CharField(max_length=15, choices=QUESTION_TYPES)
    text = models.TextField()
    exam_category = models.ForeignKey("ExamCategory", on_delete=models.CASCADE)
    correct_option = models.CharField(max_length=255, blank=True, null=True)

    # 👇 Image support
    image = models.ImageField(upload_to="questions/", blank=True, null=True)

    # ✅ Store options
    option1 = models.CharField(max_length=255, blank=True, null=True)
    option2 = models.CharField(max_length=255, blank=True, null=True)
    option3 = models.CharField(max_length=255, blank=True, null=True)
    option4 = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.text


class Exam(models.Model):
    category = models.ForeignKey(ExamCategory, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class StudentAnswer(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=200)
    is_correct = models.BooleanField()


class ExamResult(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    marks_obtained = models.FloatField()
    total_marks = models.FloatField()
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.exam.title}"
