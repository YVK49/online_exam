from django.contrib import admin
from .models import ExamCategory, Question, Exam, StudentAnswer, ExamResult

@admin.register(ExamCategory)
class ExamCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    list_filter = ('parent',)
    search_fields = ('name',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('subject', 'question_type', 'text', 'exam_category', 'correct_option')
    list_filter = ('exam_category', 'subject', 'question_type')
    search_fields = ('text', 'subject')

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('title',)

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'question', 'selected_option', 'is_correct')
    list_filter = ('exam', 'is_correct')
    search_fields = ('student__username', 'question__text')

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'marks_obtained', 'total_marks', 'completed_at')
    list_filter = ('exam',)
    search_fields = ('student__username', 'exam__title')