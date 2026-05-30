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
]