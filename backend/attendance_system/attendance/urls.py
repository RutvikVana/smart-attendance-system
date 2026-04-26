from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('analytics/', views.analytics, name='analytics'),
    path('student-report/', views.student_report, name='student_report'),
    path('student-report/<int:student_id>/', views.student_report, name='student_report_detail'),
]
