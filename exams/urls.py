from django.urls import path
from exams import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'exams'

urlpatterns = [
    path('', views.login_view, name='login'),

    # Student Dashboard (accessible via both /student/ and /student_dashboard/)
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student_dashboard/', views.student_dashboard),  # Alias for same view

    # Admin Dashboard
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Category & Exams
    path('category/<int:category_id>/', views.category_detail, name='category_detail'),
    path('exam/<int:exam_id>/', views.take_exam, name='take_exam'),
    path('exam/<int:exam_id>/submit/', views.submit_exam, name='submit_exam'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
