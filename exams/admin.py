from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
import io
from .models import ExamCategory, Question, Exam, StudentAnswer, ExamResult
from reportlab.pdfgen import canvas

c = canvas.Canvas("hello.pdf")
c.drawString(100, 750, "Hello, ReportLab!")
c.save()



@admin.register(ExamCategory)
class ExamCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    list_filter = ('parent',)
    search_fields = ('name',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_type', 'text', 'exam_category', 'correct_option', 'preview_image')
    list_filter = ('exam_category', 'question_type')
    search_fields = ('text',)

    def preview_image(self, obj):
        if obj.image:
            return format_html("<img src='{}' width='100' />", obj.image.url)
        return "No Image"
    preview_image.short_description = "Image"


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    actions = ["download_question_paper"]

    def download_question_paper(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one exam to export.", level="error")
            return
        exam = queryset.first()
        response = HttpResponse(content_type="text/csv")
        response['Content-Disposition'] = f'attachment; filename="{exam.title}_questions.csv"'
        writer = csv.writer(response)
        writer.writerow(["Question", "Type", "Subject", "Options", "Correct Answer"])
        for q in exam.questions.all():
            options = [q.option1, q.option2, q.option3, q.option4]
            writer.writerow([q.text, q.question_type, q.subject, " | ".join(filter(None, options)), q.correct_answer])
        return response
    download_question_paper.short_description = "Download Question Paper"

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
