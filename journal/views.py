from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .models import Teacher, Department

def home(request):
    return render(request, 'journal/home.html')


def teachers_list(request):
    teachers = Teacher.objects.select_related('user').all()
    return render(request, 'journal/teachers.html', {'teachers': teachers})


def departments_list(request):
    departments = Department.objects.all()
    return render(request, 'journal/departments.html', {'departments': departments})