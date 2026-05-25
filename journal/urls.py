from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('teachers/', views.teachers_list, name='teachers_list'),
    path('departments/', views.departments_list, name='departments_list'),
    path('groups/', views.groups_list, name='groups_list'),
    path('disciplines/', views.disciplines_list, name='disciplines_list'),
    path('discipline-plans/', views.discipline_plans_list, name='discipline_plans_list'),
    path('classrooms/', views.classrooms_list, name='classrooms_list'),
    path('schedule/', views.schedule_list, name='schedule_list'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]