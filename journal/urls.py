from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('teachers/', views.teachers_list, name='teachers_list'),
    path('departments/', views.departments_list, name='departments_list'),
]