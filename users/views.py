from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from journal.models import Student, Grade

# Create your views here.


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.get_full_name() or user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')

    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('home')


@login_required
def dashboard(request):
    if request.user.role and request.user.role.name == 'Студент':
        return redirect('student_dashboard')

    return render(request, 'users/dashboard.html')


@login_required
def student_dashboard(request):
    try:
        student = request.user.student
    except:
        messages.error(request, 'Профиль студента не найден.')
        return redirect('home')

    return render(request, 'users/student/dashboard.html', {'student': student})


@login_required
def student_profile(request):
    try:
        student = request.user.student
    except:
        messages.error(request, 'Профиль студента не найден.')
        return redirect('home')

    if request.method == 'POST':
        user = request.user
        user.last_name = request.POST.get('last_name')
        user.first_name = request.POST.get('first_name')
        user.patronymic = request.POST.get('patronymic')
        user.phone = request.POST.get('phone')
        user.save()

        student.special_number = request.POST.get('special_number')
        student.save()

        messages.success(request, 'Профиль успешно обновлён!')
        return redirect('student_profile')

    return render(request, 'users/student/profile.html', {
        'student': student,
    })


@login_required
def student_grades(request):
    try:
        student = request.user.student
    except:
        messages.error(request, 'Профиль студента не найден.')
        return redirect('home')

    grades = Grade.objects.filter(student=student).select_related(
        'task__lesson__schedule__discipline__plan'
    ).order_by('-created_at')

    return render(request, 'users/student/grades.html', {
        'student': student,
        'grades': grades,
    })