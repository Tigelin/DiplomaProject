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
    path('teacher/task/<int:task_id>/', views.teacher_task_grades, name='teacher_task_grades'),
    path('teacher/task/create/<int:lesson_id>/', views.teacher_task_create, name='teacher_task_create'),
    path('teacher/journal/export/<int:discipline_id>/', views.export_journal_excel, name='export_journal_excel'),
    path('teacher/journal/export/docx/<int:discipline_id>/', views.export_journal_docx, name='export_journal_docx'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/schedules/', views.admin_schedules, name='admin_schedules'),
    path('admin/schedule/create/', views.admin_schedule_create, name='admin_schedule_create'),
    path('admin/schedule/edit/<int:schedule_id>/', views.admin_schedule_edit, name='admin_schedule_edit'),
    path('admin/schedule/delete/<int:schedule_id>/', views.admin_schedule_delete, name='admin_schedule_delete'),
]