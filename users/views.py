from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from journal.models import Student, Grade, Task, Discipline, Lesson

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

    grades = Grade.objects.filter(
        student=student,
        task__isnull=False,
        task__lesson__isnull=False
    ).select_related(
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
        matrix[discipline_id][date].append(grade)

    averages = {}
    for discipline_id in disciplines_dict:
        all_grades = []
        for date in sorted_dates:
            for grade in matrix[discipline_id][date]:
                if grade.value == 1:
                    all_grades.append(2)
                else:
                    all_grades.append(grade.value)
        if all_grades:
            avg = sum(all_grades) / len(all_grades)
            averages[discipline_id] = round(avg, 2)
        else:
            averages[discipline_id] = None

    context = {
        'student': student,
        'disciplines': disciplines_dict.items(),
        'dates': sorted_dates,
        'matrix': matrix,
        'averages': averages,
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

    grades_dict = {}
    for grade in Grade.objects.filter(student=student, task__isnull=False):
        grades_dict[grade.task_id] = grade.value

    completed_task_ids = [task_id for task_id, grade in grades_dict.items() if grade >= 2]

    all_tasks = Task.objects.filter(
        lesson__schedule__discipline__group=student.group
    ).select_related(
        'lesson__schedule__discipline__plan',
        'lesson__schedule__discipline__teacher__user'
    ).distinct().order_by('lesson__schedule__date')

    if discipline_id:
        all_tasks = all_tasks.filter(lesson__schedule__discipline__id=discipline_id)

    tasks_with_status = []
    for task in all_tasks:
        if task.id in grades_dict:
            grade = grades_dict[task.id]
            is_completed = grade >= 2
            tasks_with_status.append({
                'task': task,
                'is_completed': is_completed,
                'grade': grade,
            })

    if not show_all:
        tasks_with_status = [t for t in tasks_with_status if not t['is_completed']]

    disciplines = Discipline.objects.filter(group=student.group).select_related('plan')

    context = {
        'student': student,
        'tasks_with_status': tasks_with_status,
        'disciplines': disciplines,
        'show_all': show_all,
        'selected_discipline_id': discipline_id,
    }
    return render(request, 'users/student/tasks.html', context)


@login_required
def lesson_detail(request, lesson_id):
    try:
        student = request.user.student
    except:
        messages.error(request, 'Профиль студента не найден.')
        return redirect('home')

    lesson = get_object_or_404(Lesson, id=lesson_id)

    if lesson.schedule.discipline.group != student.group:
        messages.error(request, 'У вас нет доступа к этому занятию.')
        return redirect('student_grades')

    tasks = Task.objects.filter(lesson=lesson)

    user_grades = {}
    for task in tasks:
        grade = Grade.objects.filter(student=student, task=task).first()
        user_grades[task.id] = grade.value if grade else None

    context = {
        'lesson': lesson,
        'tasks': tasks,
        'user_grades': user_grades,
    }
    return render(request, 'users/student/lesson_detail.html', context)