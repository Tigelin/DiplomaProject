from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/grades/', views.student_grades, name='student_grades'),
    path('student/tasks/', views.student_tasks, name='student_tasks'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('student/attendance/', views.student_attendance, name='student_attendance'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/profile/', views.teacher_profile, name='teacher_profile'),
    path('teacher/groups/', views.teacher_groups, name='teacher_groups'),
    path('teacher/journal/<int:discipline_id>/', views.teacher_journal, name='teacher_journal'),
    path('teacher/lesson/<int:schedule_id>/', views.teacher_lesson, name='teacher_lesson'),
    path('teacher/task/<int:task_id>/grades/', views.teacher_task_grades, name='teacher_task_grades'),
]