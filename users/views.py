from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from journal.models import Student, Grade, Task, Discipline

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
        'task__lesson__schedule__discipline__plan',
        'task__lesson__schedule'
    ).order_by('task__lesson__schedule__date')

    disciplines_dict = {}
    for grade in grades:
        discipline_name = grade.task.lesson.schedule.discipline.plan.name
        discipline_id = grade.task.lesson.schedule.discipline.id
        if discipline_id not in disciplines_dict:
            disciplines_dict[discipline_id] = discipline_name

    dates_dict = {}
    for grade in grades:
        date = grade.task.lesson.schedule.date
        if date not in dates_dict:
            dates_dict[date] = date

    sorted_dates = sorted(dates_dict.keys())

    matrix = {}
    for discipline_id in disciplines_dict:
        matrix[discipline_id] = {}
        for date in sorted_dates:
            matrix[discipline_id][date] = []

    for grade in grades:
        discipline_id = grade.task.lesson.schedule.discipline.id
        date = grade.task.lesson.schedule.date
        matrix[discipline_id][date].append(grade.value)

    context = {
        'student': student,
        'disciplines': disciplines_dict.items(),
        'dates': sorted_dates,
        'matrix': matrix,
    }
    return render(request, 'users/student/grades.html', context)


@login_required
def student_tasks(request):
    try:
        student = request.user.student
    except:
        messages.error(request, 'Профиль студента не найден.')
        return redirect('home')

    show_all = request.GET.get('show_all', 'false') == 'true'
    discipline_id = request.GET.get('discipline_id', '')

    tasks = Task.objects.filter(
        lesson__schedule__discipline__group=student.group
    ).select_related(
        'lesson__schedule__discipline__plan',
        'lesson__schedule__discipline__teacher__user'
    ).distinct().order_by('lesson__schedule__date')

    if not show_all:
        graded_task_ids = Grade.objects.filter(
            student=student,
            task__isnull=False
        ).values_list('task_id', flat=True)

        tasks = tasks.exclude(id__in=graded_task_ids)

    if discipline_id:
        tasks = tasks.filter(lesson__schedule__discipline__id=discipline_id)

    disciplines = Discipline.objects.filter(group=student.group).select_related('plan')

    context = {
        'student': student,
        'tasks': tasks,
        'disciplines': disciplines,
        'show_all': show_all,
        'selected_discipline_id': discipline_id,
    }
    return render(request, 'users/student/tasks.html', context)