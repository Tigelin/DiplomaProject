from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .models import Teacher, Department, Group, Discipline

def home(request):
    return render(request, 'journal/home.html')


def teachers_list(request):
    teachers = Teacher.objects.select_related('user').all()
    return render(request, 'journal/teachers.html', {'teachers': teachers})


def departments_list(request):
    departments = Department.objects.all()
    return render(request, 'journal/departments.html', {'departments': departments})


def groups_list(request):
    groups = Group.objects.select_related('department').all()
    return render(request, 'journal/groups.html', {'groups': groups})

def disciplines_list(request):
    disciplines = Discipline.objects.select_related('plan', 'group', 'teacher').all()
    return render(request, 'journal/disciplines.html', {'disciplines': disciplines})