from django.db import models
from django.contrib.auth.models import User

class ExamCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    question_count = models.JSONField()  # e.g., {"Physics": {"MCQ_SINGLE": 20, "NUMERICAL": 5}}

    def __str__(self):
        return self.name

class Question(models.Model):
    QUESTION_TYPES = [
        ('MCQ_SINGLE', 'MCQ Single Correct'),
        ('MCQ_MULTI', 'MCQ Multiple Correct'),
        ('NUMERICAL', 'Numerical Value'),
    ]
    exam_category = models.ForeignKey(ExamCategory, on_delete=models.CASCADE)
    subject = models.CharField(max_length=50)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='MCQ_SINGLE')
    text = models.TextField()
    image = models.ImageField(upload_to='questions/', null=True, blank=True)
    option1 = models.CharField(max_length=200, blank=True)
    option2 = models.CharField(max_length=200, blank=True)
    option3 = models.CharField(max_length=200, blank=True)
    option4 = models.CharField(max_length=200, blank=True)
    correct_option = models.CharField(max_length=200)  # 'option1' or 'option1,option3' or '42'

    def __str__(self):
        return f"{self.subject}: {self.text[:50]}"

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