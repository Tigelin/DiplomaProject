from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from django.http import HttpResponse
from urllib.parse import quote
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Sum, Count
from journal.models import (
    Grade, Task, TaskType, Discipline, Lesson, LessonFile, Attendance,
    Group, Student, Schedule, LessonType, AttendanceType, DisciplinePlan,
    Teacher, Classroom, AcademicSemester, AcademicSemesterStatus,
    Specialty, SpecialtyCurriculum, SpecialtyCurriculumItem
)
from .forms import LessonFileUploadForm
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.core.exceptions import ValidationError

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
    elif request.user.role and request.user.role.name == 'Преподаватель':
        return redirect('teacher_dashboard')
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

    paginator = Paginator(tasks_with_status, 7)
    page_number = request.GET.get('page')
    tasks_with_status = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(
        tasks_with_status.number,
        on_each_side=2,
        on_ends=1,
    )

    disciplines = Discipline.objects.filter(group=student.group).select_related('plan')

    context = {
        'student': student,
        'tasks_with_status': tasks_with_status,
        'disciplines': disciplines,
        'show_all': show_all,
        'selected_discipline_id': discipline_id,
        'page_range': page_range,
        'ellipsis': paginator.ELLIPSIS,
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

    tasks_with_grades = []
    for task in tasks:
        grade = Grade.objects.filter(student=student, task=task).first()
        if grade:
            tasks_with_grades.append({
                'task': task,
                'grade': grade.value,
            })

    files = LessonFile.objects.filter(lesson=lesson)

    context = {
        'lesson': lesson,
        'tasks_with_grades': tasks_with_grades,
        'files': files,
    }
    return render(request, 'users/student/lesson_detail.html', context)


@login_required
def student_attendance(request):
    try:
        student = request.user.student
    except:
        messages.error(request, 'Профиль студента не найден.')
        return redirect('home')

    lessons = Lesson.objects.filter(
        schedule__discipline__group=student.group
    ).select_related(
        'schedule__discipline__plan',
        'schedule'
    ).order_by('schedule__date', 'schedule__lesson_number')

    attendances = {att.lesson_id: att for att in Attendance.objects.filter(student=student)}

    disciplines_dict = {}
    for lesson in lessons:
        discipline_name = lesson.schedule.discipline.plan.name
        discipline_id = lesson.schedule.discipline.id
        if discipline_id not in disciplines_dict:
            disciplines_dict[discipline_id] = discipline_name

    lessons_list = []
    for lesson in lessons:
        lessons_list.append({
            'id': lesson.id,
            'date': lesson.schedule.date,
            'lesson_number': lesson.schedule.lesson_number,
            'discipline_id': lesson.schedule.discipline.id,
        })

    matrix = {}
    for discipline_id in disciplines_dict:
        matrix[discipline_id] = {}
        for lesson in lessons_list:
            matrix[discipline_id][lesson['date']] = matrix[discipline_id].get(lesson['date'], {})
            matrix[discipline_id][lesson['date']][lesson['lesson_number']] = None

    for lesson in lessons:
        discipline_id = lesson.schedule.discipline.id
        date = lesson.schedule.date
        lesson_number = lesson.schedule.lesson_number
        attendance = attendances.get(lesson.id)
        if attendance:
            matrix[discipline_id][date][lesson_number] = attendance.attendance_type.name
        else:
            matrix[discipline_id][date][lesson_number] = 'Присутствовал'

    total = len(lessons)
    present = sum(1 for att in attendances.values() if att.attendance_type.name == 'Присутствовал')

    present += (total - len(attendances))
    absent = total - present
    attendance_percent = round((present / total * 100) if total > 0 else 0)

    context = {
        'student': student,
        'disciplines': disciplines_dict.items(),
        'lessons': lessons_list,
        'matrix': matrix,
        'total': total,
        'present': present,
        'absent': absent,
        'attendance_percent': attendance_percent,
    }
    return render(request, 'users/student/attendance.html', context)


@login_required
def teacher_dashboard(request):
    try:
        teacher = request.user.teacher
    except:
        messages.error(request, 'Профиль преподавателя не найден.')
        return redirect('home')

    context = {
        'teacher': teacher,
    }
    return render(request, 'users/teacher/dashboard.html', context)


@login_required
def teacher_profile(request):
    try:
        teacher = request.user.teacher
    except:
        messages.error(request, 'Профиль преподавателя не найден.')
        return redirect('home')

    context = {
        'teacher': teacher,
    }
    return render(request, 'users/teacher/profile.html', context)


@login_required
def teacher_groups(request):
    try:
        teacher = request.user.teacher
    except:
        messages.error(request, 'Профиль преподавателя не найден.')
        return redirect('home')

    disciplines = Discipline.objects.filter(
        teacher=teacher
    ).select_related(
        'plan',
        'group__specialty',
    ).annotate(
        actual_hours=Sum('schedule__lesson__hours')
    ).order_by(
        '-group__year',
        'group__name',
        'plan__name',
    )

    search = request.GET.get('search', '')
    if search:
        disciplines = disciplines.filter(
            Q(plan__name__icontains=search) |
            Q(group__name__icontains=search) |
            Q(group__specialty__name__icontains=search)
        )

    paginator = Paginator(disciplines, 15)
    page_number = request.GET.get('page')
    disciplines = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(
        disciplines.number,
        on_each_side=2,
        on_ends=1,
    )

    context = {
        'teacher': teacher,
        'disciplines': disciplines,
        'search': search,
        'page_range': page_range,
        'ellipsis': paginator.ELLIPSIS,
    }
    return render(request, 'users/teacher/groups.html', context)


@login_required
def teacher_journal(request, discipline_id):
    try:
        teacher = request.user.teacher
    except:
        messages.error(request, 'Профиль преподавателя не найден.')
        return redirect('home')

    discipline = get_object_or_404(Discipline, id=discipline_id)

    if discipline.teacher != teacher:
        messages.error(request, 'У вас нет доступа к этой дисциплине.')
        return redirect('teacher_groups')

    students = Student.objects.filter(group=discipline.group).select_related('user').order_by('user__last_name')

    schedules = Schedule.objects.filter(
        discipline=discipline
    ).select_related('classroom').order_by('date', 'lesson_number')

    for schedule in schedules:
        lesson = Lesson.objects.filter(schedule=schedule).first()
        schedule.has_lesson = lesson is not None
        if schedule.has_lesson:
            schedule.lesson = lesson
            schedule.lesson_type = lesson.lesson_type.name if lesson.lesson_type else '—'
            schedule.tasks = (
                Task.objects
                .filter(lesson=lesson)
                .select_related('task_type')
            )
        else:
            schedule.lesson_type = None
            schedule.tasks = []
            schedule.lesson = None

    grades_matrix = {}
    for student in students:
        grades_matrix[student.id] = {}
        for schedule in schedules:
            if schedule.has_lesson:
                for task in schedule.tasks:
                    grades_matrix[student.id][task.id] = None

    grades = Grade.objects.filter(
        task__lesson__schedule__discipline=discipline
    ).select_related('student', 'task')

    for grade in grades:
        student_id = grade.student.id
        task_id = grade.task.id
        if student_id in grades_matrix and task_id in grades_matrix[student_id]:
            grades_matrix[student_id][task_id] = grade.value

    attendance_matrix = {}
    for student in students:
        attendance_matrix[student.id] = {}
        for schedule in schedules:
            if schedule.has_lesson:
                attendance_matrix[student.id][schedule.lesson.id] = 'Присутствовал'

    attendances = Attendance.objects.filter(
        lesson__schedule__discipline=discipline
    ).select_related('student', 'lesson', 'attendance_type')

    for attendance in attendances:
        student_id = attendance.student.id
        lesson_id = attendance.lesson.id

        if student_id in attendance_matrix and lesson_id in attendance_matrix[student_id]:
            if attendance.attendance_type:
                attendance_matrix[student_id][lesson_id] = attendance.attendance_type.name
            else:
                attendance_matrix[student_id][lesson_id] = '—'

    context = {
        'teacher': teacher,
        'discipline': discipline,
        'students': students,
        'schedules': schedules,
        'grades_matrix': grades_matrix,
        'attendance_matrix': attendance_matrix,
    }
    return render(request, 'users/teacher/journal.html', context)


@login_required
def teacher_lesson(request, schedule_id):
    try:
        teacher = request.user.teacher
    except:
        messages.error(request, 'Профиль преподавателя не найден.')
        return redirect('home')

    schedule = get_object_or_404(Schedule, id=schedule_id)

    if schedule.discipline.teacher != teacher:
        messages.error(request, 'У вас нет доступа к этому занятию.')
        return redirect('teacher_groups')

    lesson = Lesson.objects.filter(schedule=schedule).first()
    upload_form = LessonFileUploadForm()

    if request.method == 'POST':
        if 'save_lesson' in request.POST:
            if not lesson:
                lesson = Lesson.objects.create(schedule=schedule, hours=2)

            lesson.topic = request.POST.get('topic', '')
            lesson_type_id = request.POST.get('lesson_type')
            if lesson_type_id:
                lesson.lesson_type_id = lesson_type_id
            lesson.hours = 2
            lesson.save()

            messages.success(request, 'Занятие сохранено.')
            return redirect('teacher_lesson', schedule_id=schedule.id)

        elif 'add_task' in request.POST:
            if lesson:
                task_type_id = request.POST.get('task_type', '')

                if not task_type_id.isdigit():
                    messages.error(request, 'Выберите тип задания.')
                    return redirect('teacher_lesson', schedule_id=schedule.id)

                task_type = TaskType.objects.filter(id=task_type_id).first()

                if not task_type:
                    messages.error(request, 'Выбранный тип задания не найден.')
                    return redirect('teacher_lesson', schedule_id=schedule.id)

                Task.objects.create(
                    name=request.POST.get('task_name'),
                    task_type=task_type,
                    lesson=lesson,
                    description=request.POST.get('task_description', '')
                )
                messages.success(request, 'Задание добавлено.')
            else:
                messages.error(request, 'Сначала сохраните занятие.')
            return redirect('teacher_lesson', schedule_id=schedule.id)

        elif 'upload_file' in request.POST:
            if not lesson:
                messages.error(request, 'Сначала сохраните занятие.')
                return redirect('teacher_lesson', schedule_id=schedule.id)

            upload_form = LessonFileUploadForm(
                request.POST,
                request.FILES
            )

            if upload_form.is_valid():
                LessonFile.objects.create(
                    name=upload_form.cleaned_data['file_name'],
                    lesson=lesson,
                    file=upload_form.cleaned_data['file']
                )
                messages.success(request, 'Файл загружен.')
                return redirect('teacher_lesson', schedule_id=schedule.id)

            messages.error(request, 'Не удалось загрузить файл.')

    created = lesson is None

    lesson_types = LessonType.objects.all()
    files = LessonFile.objects.filter(lesson=lesson) if lesson else []
    task_types = TaskType.objects.order_by('name')
    tasks = (
        Task.objects
        .filter(lesson=lesson)
        .select_related('task_type')
        if lesson else []
    )

    context = {
        'teacher': teacher,
        'schedule': schedule,
        'lesson': lesson,
        'created': created,
        'lesson_types': lesson_types,
        'files': files,
        'tasks': tasks,
        'task_types': task_types,
        'upload_form': upload_form,
    }
    return render(request, 'users/teacher/lesson.html', context)


@login_required
def teacher_lesson_attendance(request, lesson_id):
    try:
        teacher = request.user.teacher
    except:
        messages.error(request, 'Профиль преподавателя не найден.')
        return redirect('home')

    lesson = get_object_or_404(Lesson, id=lesson_id)
    schedule = lesson.schedule

    if schedule.discipline.teacher != teacher:
        messages.error(request, 'У вас нет доступа к этому занятию.')
        return redirect('teacher_groups')

    students = Student.objects.filter(
        group=schedule.discipline.group
    ).select_related('user').order_by('user__last_name')

    attendance_types = AttendanceType.objects.all().order_by('id')
    attendance_types_by_id = {
        str(attendance_type.id): attendance_type
        for attendance_type in attendance_types
    }

    present_type = attendance_types.filter(name='Присутствовал').first()

    if not present_type:
        messages.error(request, 'Тип посещаемости «Присутствовал» не найден.')
        return redirect('teacher_lesson', schedule_id=schedule.id)

    attendance_statuses = {
        student.id: present_type.id
        for student in students
    }

    attendances = Attendance.objects.filter(
        lesson=lesson,
        student__in=students,
        attendance_type__isnull=False
    )

    for attendance in attendances:
        if str(attendance.attendance_type_id) in attendance_types_by_id:
            attendance_statuses[attendance.student_id] = attendance.attendance_type_id

    if request.method == 'POST':
        submitted_statuses = {}

        for student in students:
            attendance_type_id = request.POST.get(f'attendance_{student.id}')

            if attendance_type_id not in attendance_types_by_id:
                messages.error(request, 'Выберите статус посещаемости для каждого студента.')
                break

            submitted_statuses[student.id] = attendance_type_id
            attendance_statuses[student.id] = int(attendance_type_id)
        else:
            with transaction.atomic():
                for student in students:
                    attendance_type = attendance_types_by_id[
                        submitted_statuses[student.id]
                    ]

                    if attendance_type.id == present_type.id:
                        Attendance.objects.filter(
                            lesson=lesson,
                            student=student
                        ).delete()
                    else:
                        Attendance.objects.update_or_create(
                            lesson=lesson,
                            student=student,
                            defaults={'attendance_type': attendance_type}
                        )

            messages.success(request, 'Посещаемость сохранена.')
            return redirect('teacher_lesson_attendance', lesson_id=lesson.id)

    context = {
        'teacher': teacher,
        'lesson': lesson,
        'schedule': schedule,
        'students': students,
        'attendance_types': attendance_types,
        'attendance_statuses': attendance_statuses,
    }
    return render(request, 'users/teacher/lesson_attendance.html', context)


@login_required
def teacher_task_grades(request, task_id):
    try:
        teacher = request.user.teacher
    except:
        messages.error(request, 'Профиль преподавателя не найден.')
        return redirect('home')

    task = get_object_or_404(Task.objects.select_related('task_type'), id=task_id)
    lesson = task.lesson
    schedule = lesson.schedule

    if schedule.discipline.teacher != teacher:
        messages.error(request, 'У вас нет доступа к этому заданию.')
        return redirect('teacher_groups')

    students = list(Student.objects.filter(
        group=schedule.discipline.group
    ).select_related('user').order_by('user__last_name'))

    attendance_statuses = {
        student.id: 'Присутствовал'
        for student in students
    }

    attendances = Attendance.objects.filter(
        lesson=lesson,
        student__in=students,
        attendance_type__isnull=False
    ).select_related('attendance_type')

    for attendance in attendances:
        attendance_statuses[attendance.student_id] = attendance.attendance_type.name

    if request.method == 'POST':
        if 'delete_task' in request.POST:
            task.delete()
            messages.success(request, 'Задание удалено.')
            return redirect('teacher_journal', discipline_id=schedule.discipline.id)

        elif 'save_task' in request.POST:
            task_type_id = request.POST.get('task_type', '')

            if not task_type_id.isdigit():
                messages.error(request, 'Выберите тип задания.')
                return redirect('teacher_task_grades', task_id=task.id)

            task_type = TaskType.objects.filter(id=task_type_id).first()

            if not task_type:
                messages.error(request, 'Выбранный тип задания не найден.')
                return redirect('teacher_task_grades', task_id=task.id)

            task.task_type = task_type
            task.name = request.POST.get('task_name')
            task.description = request.POST.get('task_description', '')
            task.save()

            messages.success(request, 'Задание сохранено.')
            return redirect('teacher_task_grades', task_id=task.id)

        elif 'save_grades' in request.POST:
            submitted_grades = {}
            submitted_required_student_ids = set()

            for student in students:
                grade_value = request.POST.get(f'grade_{student.id}', '').strip()

                if f'required_{student.id}' in request.POST:
                    submitted_required_student_ids.add(student.id)

                if grade_value:
                    if not grade_value.isdigit() or not 2 <= int(grade_value) <= 5:
                        messages.error(
                            request,
                            'Оценка должна быть целым числом от 2 до 5.'
                        )
                        return redirect('teacher_task_grades', task_id=task.id)

                    submitted_grades[student.id] = int(grade_value)

            with transaction.atomic():
                task.required_students.set(submitted_required_student_ids)

                for student in students:
                    grade_value = submitted_grades.get(student.id)

                    if grade_value is not None:
                        Grade.objects.update_or_create(
                            task=task,
                            student=student,
                            defaults={'value': grade_value}
                        )

                    elif student.id in submitted_required_student_ids:
                        Grade.objects.update_or_create(
                            task=task,
                            student=student,
                            defaults={'value': 1}
                        )

                    else:
                        Grade.objects.filter(
                            task=task,
                            student=student
                        ).delete()

            messages.success(request, 'Оценки сохранены.')

            return redirect('teacher_task_grades', task_id=task.id)

    grades = {
        student.id: None
        for student in students
    }

    for grade in Grade.objects.filter(task=task, student__in=students):
        if 2 <= grade.value <= 5:
            grades[grade.student_id] = grade.value

    required_student_ids = set(
        task.required_students.filter(
            group=schedule.discipline.group
        ).values_list('id', flat=True)
    )

    task_types = TaskType.objects.order_by('name')

    context = {
        'teacher': teacher,
        'task': task,
        'lesson': lesson,
        'schedule': schedule,
        'students': students,
        'grades': grades,
        'attendance_statuses': attendance_statuses,
        'required_student_ids': required_student_ids,
        'task_types': task_types,
    }

    return render(request, 'users/teacher/task_grades.html', context)


@login_required
def teacher_task_create(request, lesson_id):
    try:
        teacher = request.user.teacher
    except:
        messages.error(request, 'Профиль преподавателя не найден.')
        return redirect('home')

    lesson = get_object_or_404(Lesson, id=lesson_id)

    if lesson.schedule.discipline.teacher != teacher:
        messages.error(request, 'У вас нет доступа.')
        return redirect('teacher_groups')

    task_type = TaskType.objects.order_by('id').first()

    if not task_type:
        messages.error(
            request,
            'В справочнике нет ни одного типа задания.'
        )
        return redirect(
            'teacher_journal',
            discipline_id=lesson.schedule.discipline.id
        )

    task = Task.objects.create(
        lesson=lesson,
        task_type=task_type,
        name='Новое задание'
    )

    return redirect('teacher_task_grades', task_id=task.id)


@login_required
def export_journal_excel(request, discipline_id):
    try:
        teacher = request.user.teacher
    except:
        messages.error(request, 'Профиль преподавателя не найден.')
        return redirect('home')

    discipline = get_object_or_404(Discipline, id=discipline_id)

    if discipline.teacher != teacher:
        messages.error(request, 'У вас нет доступа к этой дисциплине.')
        return redirect('teacher_groups')

    students = Student.objects.filter(group=discipline.group).select_related('user').order_by('user__last_name')

    schedules = Schedule.objects.filter(
        discipline=discipline
    ).select_related('classroom').order_by('date', 'lesson_number')

    for schedule in schedules:
        lesson = Lesson.objects.filter(schedule=schedule).first()
        schedule.has_lesson = lesson is not None
        if schedule.has_lesson:
            schedule.lesson = lesson
            schedule.lesson_type = lesson.lesson_type.name if lesson.lesson_type else '—'
            schedule.tasks = Task.objects.filter(lesson=lesson).select_related('task_type')
            schedule.topic = lesson.topic if lesson.topic else '—'
        else:
            schedule.lesson_type = None
            schedule.tasks = []
            schedule.lesson = None
            schedule.topic = None

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Журнал_{discipline.plan.name}"

    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    header_fill = PatternFill(start_color="2c3e50", end_color="2c3e50", fill_type="solid")
    header_font = Font(color="ffffff", bold=True)
    center_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    row = 1
    col = 1

    ws.cell(row=row, column=col).value = "Журнал оценок"
    ws.cell(row=row, column=col).font = Font(bold=True, size=14)
    ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col + 1 + len(schedules))
    row += 2

    ws.cell(row=row, column=col).value = f"Дисциплина: {discipline.plan.name}"
    ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col + 1 + len(schedules))
    row += 1

    ws.cell(row=row, column=col).value = f"Группа: {discipline.group.name}"
    ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col + 1 + len(schedules))
    row += 1

    ws.cell(row=row,
            column=col).value = f"Преподаватель: {teacher.user.last_name} {teacher.user.first_name} {teacher.user.patronymic}"
    ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col + 1 + len(schedules))
    row += 2

    first_header_row = row
    col = 1

    ws.cell(row=first_header_row, column=col).value = "№"
    ws.cell(row=first_header_row, column=col).fill = header_fill
    ws.cell(row=first_header_row, column=col).font = header_font
    ws.cell(row=first_header_row, column=col).alignment = center_alignment
    ws.cell(row=first_header_row, column=col).border = thin_border
    col += 1

    ws.cell(row=first_header_row, column=col).value = "Студент"
    ws.cell(row=first_header_row, column=col).fill = header_fill
    ws.cell(row=first_header_row, column=col).font = header_font
    ws.cell(row=first_header_row, column=col).alignment = center_alignment
    ws.cell(row=first_header_row, column=col).border = thin_border
    col += 1

    for schedule in schedules:
        if schedule.has_lesson and schedule.tasks:
            first_col = col
            for task in schedule.tasks:
                col += 1
            last_col = col - 1
            cell_value = f"{schedule.date.strftime('%d.%m.%Y')} ({schedule.lesson_number} пара)\n{schedule.topic}"
            ws.cell(row=first_header_row, column=first_col).value = cell_value
            ws.cell(row=first_header_row, column=first_col).fill = header_fill
            ws.cell(row=first_header_row, column=first_col).font = header_font
            ws.cell(row=first_header_row, column=first_col).alignment = center_alignment
            ws.cell(row=first_header_row, column=first_col).border = thin_border
            if first_col != last_col:
                ws.merge_cells(start_row=first_header_row, start_column=first_col, end_row=first_header_row,
                               end_column=last_col)
        elif schedule.has_lesson:
            cell_value = f"{schedule.date.strftime('%d.%m.%Y')} ({schedule.lesson_number} пара)\n{schedule.topic}"
            ws.cell(row=first_header_row, column=col).value = cell_value
            ws.cell(row=first_header_row, column=col).fill = header_fill
            ws.cell(row=first_header_row, column=col).font = header_font
            ws.cell(row=first_header_row, column=col).alignment = center_alignment
            ws.cell(row=first_header_row, column=col).border = thin_border
            col += 1

    second_header_row = first_header_row + 1
    col = 1

    for i in range(1, 3):
        ws.cell(row=second_header_row, column=i).value = ""
        ws.cell(row=second_header_row, column=i).fill = header_fill
        ws.cell(row=second_header_row, column=i).border = thin_border
        if i == 1:
            ws.merge_cells(start_row=first_header_row, start_column=1, end_row=second_header_row, end_column=1)
        elif i == 2:
            ws.merge_cells(start_row=first_header_row, start_column=2, end_row=second_header_row, end_column=2)

    col = 3

    for schedule in schedules:
        if schedule.has_lesson and schedule.tasks:
            for task in schedule.tasks:
                ws.cell(row=second_header_row, column=col).value = f"{task.task_type.abbreviation} — {task.name}"
                ws.cell(row=second_header_row, column=col).fill = header_fill
                ws.cell(row=second_header_row, column=col).font = header_font
                ws.cell(row=second_header_row, column=col).alignment = center_alignment
                ws.cell(row=second_header_row, column=col).border = thin_border
                col += 1
        elif schedule.has_lesson:
            col += 1

    ws.row_dimensions[first_header_row].height = 40
    ws.row_dimensions[second_header_row].height = 30

    row = second_header_row + 1

    for idx, student in enumerate(students, start=1):
        col = 1
        ws.cell(row=row, column=col).value = idx
        ws.cell(row=row, column=col).alignment = center_alignment
        ws.cell(row=row, column=col).border = thin_border
        col += 1

        ws.cell(row=row,
                column=col).value = f"{student.user.last_name} {student.user.first_name} {student.user.patronymic}"
        ws.cell(row=row, column=col).alignment = left_alignment
        ws.cell(row=row, column=col).border = thin_border
        col += 1

        for schedule in schedules:
            if schedule.has_lesson and schedule.tasks:
                for task in schedule.tasks:
                    grade = Grade.objects.filter(task=task, student=student).first()
                    grade_value = grade.value if grade else ''
                    ws.cell(row=row, column=col).value = grade_value
                    ws.cell(row=row, column=col).alignment = center_alignment
                    ws.cell(row=row, column=col).border = thin_border

                    if grade_value == 1 or grade_value == 2:
                        ws.cell(row=row, column=col).fill = PatternFill(start_color="ffcccc", end_color="ffcccc",
                                                                        fill_type="solid")
                    elif grade_value == 3:
                        ws.cell(row=row, column=col).fill = PatternFill(start_color="ffffcc", end_color="ffffcc",
                                                                        fill_type="solid")
                    elif grade_value == 4 or grade_value == 5:
                        ws.cell(row=row, column=col).fill = PatternFill(start_color="ccffcc", end_color="ccffcc",
                                                                        fill_type="solid")

                    col += 1
            elif schedule.has_lesson:
                ws.cell(row=row, column=col).value = ''
                ws.cell(row=row, column=col).alignment = center_alignment
                ws.cell(row=row, column=col).border = thin_border
                col += 1

        row += 1

    for col_num in range(1, ws.max_column + 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_num)].width = 15

    current_date = datetime.now().strftime('%d.%m.%Y')
    filename = f"{discipline.plan.name}_{discipline.group.name}_{current_date}.xlsx"
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
    wb.save(response)
    return response


@login_required
def export_journal_docx(request, discipline_id):
    try:
        teacher = request.user.teacher
    except:
        messages.error(request, 'Профиль преподавателя не найден.')
        return redirect('home')

    discipline = get_object_or_404(Discipline, id=discipline_id)

    if discipline.teacher != teacher:
        messages.error(request, 'У вас нет доступа к этой дисциплине.')
        return redirect('teacher_groups')

    students = Student.objects.filter(group=discipline.group).select_related('user').order_by('user__last_name')

    schedules = Schedule.objects.filter(
        discipline=discipline
    ).select_related('classroom').order_by('date', 'lesson_number')

    for schedule in schedules:
        lesson = Lesson.objects.filter(schedule=schedule).first()
        schedule.has_lesson = lesson is not None
        if schedule.has_lesson:
            schedule.lesson = lesson
            schedule.lesson_type = lesson.lesson_type.name if lesson.lesson_type else '—'
            schedule.tasks = Task.objects.filter(lesson=lesson).select_related('task_type')
            schedule.topic = lesson.topic if lesson.topic else '—'
        else:
            schedule.lesson_type = None
            schedule.tasks = []
            schedule.lesson = None
            schedule.topic = None

    doc = Document()

    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)

    section = doc.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(1.5)

    title = doc.add_heading('Журнал оценок', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(f'Дисциплина: {discipline.plan.name}')
    doc.add_paragraph(f'Группа: {discipline.group.name}')
    doc.add_paragraph(f'Преподаватель: {teacher.user.last_name} {teacher.user.first_name} {teacher.user.patronymic}')
    doc.add_paragraph()

    table_rows = 2 + len(students)
    table_cols = 2
    for schedule in schedules:
        if schedule.has_lesson and schedule.tasks:
            table_cols += len(schedule.tasks)
        elif schedule.has_lesson:
            table_cols += 1

    table = doc.add_table(rows=table_rows, cols=table_cols)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for row in table.rows:
        for cell in row.cells:
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    col = 0
    table.cell(0, col).text = '№'
    table.cell(1, col).text = '№'
    col += 1
    table.cell(0, col).text = 'Студент'
    table.cell(1, col).text = 'Студент'
    col += 1

    for schedule in schedules:
        if schedule.has_lesson and schedule.tasks:
            first_col = col
            for task in schedule.tasks:
                col += 1
            last_col = col - 1
            cell_value = f"{schedule.date.strftime('%d.%m.%Y')} ({schedule.lesson_number} пара)\n{schedule.topic}"
            table.cell(0, first_col).text = cell_value
            if first_col != last_col:
                table.cell(0, first_col).merge(table.cell(0, last_col))
        elif schedule.has_lesson:
            cell_value = f"{schedule.date.strftime('%d.%m.%Y')} ({schedule.lesson_number} пара)\n{schedule.topic}"
            table.cell(0, col).text = cell_value
            col += 1

    col = 2
    for schedule in schedules:
        if schedule.has_lesson and schedule.tasks:
            for task in schedule.tasks:
                table.cell(1, col).text = f"{task.task_type.abbreviation} — {task.name}"
                col += 1
        elif schedule.has_lesson:
            col += 1

    for idx, student in enumerate(students, start=1):
        row = idx + 1
        col = 0
        table.cell(row, col).text = str(idx)
        col += 1
        table.cell(row, col).text = f"{student.user.last_name} {student.user.first_name} {student.user.patronymic}"
        col += 1

        for schedule in schedules:
            if schedule.has_lesson and schedule.tasks:
                for task in schedule.tasks:
                    grade = Grade.objects.filter(task=task, student=student).first()
                    grade_value = grade.value if grade else ''
                    table.cell(row, col).text = str(grade_value) if grade_value else ''
                    col += 1
            elif schedule.has_lesson:
                col += 1

    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.size = Pt(10)

    current_date = datetime.now().strftime('%d.%m.%Y')
    filename = f"{discipline.plan.name}_{discipline.group.name}_{current_date}.docx"

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
    doc.save(response)
    return response


@staff_member_required
def admin_dashboard(request):
    return render(request, 'users/admin/dashboard.html')


@staff_member_required
def admin_semesters(request):
    semesters = AcademicSemester.objects.select_related('status').order_by('-start_date')

    search = request.GET.get('search', '')
    if search:
        semesters = semesters.filter(
            Q(start_year__icontains=search) |
            Q(status__name__icontains=search)
        )

    paginator = Paginator(semesters, 12)
    page_number = request.GET.get('page')
    semesters = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(
        semesters.number,
        on_each_side=2,
        on_ends=1,
    )

    context = {
        'semesters': semesters,
        'search': search,
        'page_range': page_range,
        'ellipsis': paginator.ELLIPSIS,
    }
    return render(request, 'users/admin/semesters.html', context)


@staff_member_required
def admin_semester_create(request):
    start_year = ''
    semester_number = '1'
    start_date = ''
    end_date = ''

    if request.method == 'POST':
        start_year = request.POST.get('start_year')
        semester_number = request.POST.get('semester_number')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if semester_number not in ['1', '2']:
            messages.error(request, 'Выберите номер семестра.')
        else:
            draft_status = get_object_or_404(
                AcademicSemesterStatus,
                code='DRAFT'
            )

            semester = AcademicSemester(
                start_year=start_year,
                is_first_semester=semester_number == '1',
                start_date=start_date,
                end_date=end_date,
                status=draft_status
            )

            try:
                semester.full_clean()
                semester.save()
                messages.success(request, 'Учебный семестр добавлен.')
                return redirect('admin_semesters')
            except ValidationError as error:
                for message in error.messages:
                    messages.error(request, message)

    context = {
        'start_year': start_year,
        'semester_number': semester_number,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'users/admin/semester_form.html', context)


@staff_member_required
def admin_semester_edit(request, semester_id):
    semester = get_object_or_404(
        AcademicSemester.objects.select_related('status'),
        id=semester_id
    )

    if semester.status.code != 'DRAFT':
        messages.error(request, 'Изменять можно только черновик семестра.')
        return redirect('admin_semesters')

    start_year = semester.start_year
    semester_number = str(semester.number)
    start_date = semester.start_date.strftime('%Y-%m-%d')
    end_date = semester.end_date.strftime('%Y-%m-%d')

    if request.method == 'POST':
        start_year = request.POST.get('start_year')
        semester_number = request.POST.get('semester_number')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if semester_number not in ['1', '2']:
            messages.error(request, 'Выберите номер семестра.')
        else:
            semester.start_year = start_year
            semester.is_first_semester = semester_number == '1'
            semester.start_date = start_date
            semester.end_date = end_date

            try:
                semester.full_clean()
                semester.save()
                messages.success(request, 'Учебный семестр обновлён.')
                return redirect('admin_semesters')
            except ValidationError as error:
                for message in error.messages:
                    messages.error(request, message)

    context = {
        'semester': semester,
        'start_year': start_year,
        'semester_number': semester_number,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'users/admin/semester_form.html', context)


@staff_member_required
def admin_curriculums(request):
    specialties = Specialty.objects.order_by('name')
    selected_specialty = None
    study_semester = None
    semester_numbers = []
    curriculums = SpecialtyCurriculum.objects.none()
    show_archived = request.GET.get('show_archived') == '1'

    specialty_id = request.GET.get('specialty_id')
    semester_number = request.GET.get('study_semester')

    if specialty_id:
        selected_specialty = get_object_or_404(
            Specialty,
            id=specialty_id
        )
        semester_numbers = range(
            1,
            selected_specialty.duration_semesters + 1
        )

    if selected_specialty and semester_number:
        try:
            study_semester = int(semester_number)
        except ValueError:
            messages.error(request, 'Выберите семестр обучения.')
        else:
            if study_semester < 1 or study_semester > selected_specialty.duration_semesters:
                messages.error(request, 'Выбран неверный семестр обучения.')
                study_semester = None
            else:
                curriculums = SpecialtyCurriculum.objects.filter(
                    specialty=selected_specialty,
                    study_semester=study_semester
                ).annotate(
                    item_count=Count('items')
                ).order_by(
                    'name'
                )

                if not show_archived:
                    curriculums = curriculums.filter(is_archived=False)

    context = {
        'specialties': specialties,
        'selected_specialty': selected_specialty,
        'semester_numbers': semester_numbers,
        'study_semester': study_semester,
        'curriculums': curriculums,
        'show_archived': show_archived,
    }
    return render(request, 'users/admin/curriculums.html', context)


@staff_member_required
def admin_curriculum_create(request):
    specialties = Specialty.objects.order_by('name')
    selected_specialty = None
    name = ''
    study_semester = request.GET.get('study_semester', '')

    specialty_id = request.GET.get('specialty_id')

    if specialty_id:
        selected_specialty = get_object_or_404(
            Specialty,
            id=specialty_id
        )

    if request.method == 'POST':
        name = request.POST.get('name')
        study_semester = request.POST.get('study_semester')
        selected_specialty = get_object_or_404(
            Specialty,
            id=request.POST.get('specialty_id')
        )

        curriculum = SpecialtyCurriculum(
            name=name,
            specialty=selected_specialty,
            study_semester=study_semester
        )

        try:
            curriculum.full_clean()
            curriculum.save()
            messages.success(request, 'Учебный план добавлен.')
            return redirect(
                f"{reverse('admin_curriculums')}?"
                f"specialty_id={curriculum.specialty_id}&"
                f"study_semester={curriculum.study_semester}"
            )
        except ValidationError as error:
            for message in error.messages:
                messages.error(request, message)

    context = {
        'specialties': specialties,
        'selected_specialty': selected_specialty,
        'name': name,
        'study_semester': study_semester,
    }
    return render(request, 'users/admin/curriculum_form.html', context)


@staff_member_required
def admin_curriculum_edit(request, curriculum_id):
    curriculum = get_object_or_404(
        SpecialtyCurriculum.objects.select_related('specialty'),
        id=curriculum_id
    )

    if curriculum.is_approved or curriculum.is_archived:
        messages.error(
            request,
            'Изменять можно только черновик учебного плана.'
        )
        return redirect(
            f"{reverse('admin_curriculums')}?"
            f"specialty_id={curriculum.specialty_id}&"
            f"study_semester={curriculum.study_semester}"
        )

    specialties = Specialty.objects.order_by('name')
    selected_specialty = curriculum.specialty
    name = curriculum.name
    study_semester = curriculum.study_semester
    return_specialty_id = curriculum.specialty_id
    return_study_semester = curriculum.study_semester

    if request.method == 'POST':
        name = request.POST.get('name')
        study_semester = request.POST.get('study_semester')
        selected_specialty = get_object_or_404(
            Specialty,
            id=request.POST.get('specialty_id')
        )

        curriculum.name = name
        curriculum.specialty = selected_specialty
        curriculum.study_semester = study_semester

        try:
            curriculum.full_clean()
            curriculum.save()
            messages.success(request, 'Учебный план изменён.')
            return redirect(
                f"{reverse('admin_curriculums')}?"
                f"specialty_id={curriculum.specialty_id}&"
                f"study_semester={curriculum.study_semester}"
            )
        except ValidationError as error:
            for message in error.messages:
                messages.error(request, message)

    context = {
        'curriculum': curriculum,
        'specialties': specialties,
        'selected_specialty': selected_specialty,
        'name': name,
        'study_semester': study_semester,
        'return_specialty_id': return_specialty_id,
        'return_study_semester': return_study_semester,
    }
    return render(request, 'users/admin/curriculum_form.html', context)


@staff_member_required
def admin_curriculum_detail(request, curriculum_id):
    curriculum = get_object_or_404(
        SpecialtyCurriculum.objects.select_related('specialty'),
        id=curriculum_id
    )

    item_search = request.GET.get('item_search', '')
    items = curriculum.items.select_related('plan').order_by('plan__name')

    if item_search:
        items = items.filter(plan__name__icontains=item_search)

    item_paginator = Paginator(items, 8)
    items = item_paginator.get_page(request.GET.get('item_page'))
    item_page_range = item_paginator.get_elided_page_range(
        items.number,
        on_each_side=2,
        on_ends=1,
    )
    item_ellipsis = item_paginator.ELLIPSIS

    is_draft = not curriculum.is_approved and not curriculum.is_archived
    available_search = request.GET.get('available_search', '')
    available_plans = DisciplinePlan.objects.none()
    available_page_range = []
    available_ellipsis = None

    if is_draft:
        item_plan_ids = curriculum.items.values_list('plan_id', flat=True)
        available_plans = DisciplinePlan.objects.filter(
            is_approved=True,
            is_archived=False
        ).exclude(
            id__in=item_plan_ids
        ).order_by(
            'name'
        )

        if available_search:
            available_plans = available_plans.filter(
                name__icontains=available_search
            )

        available_paginator = Paginator(available_plans, 8)
        available_plans = available_paginator.get_page(
            request.GET.get('available_page')
        )
        available_page_range = available_paginator.get_elided_page_range(
            available_plans.number,
            on_each_side=2,
            on_ends=1,
        )
        available_ellipsis = available_paginator.ELLIPSIS

    context = {
        'curriculum': curriculum,
        'items': items,
        'item_search': item_search,
        'item_page_range': item_page_range,
        'item_ellipsis': item_ellipsis,
        'is_draft': is_draft,
        'available_plans': available_plans,
        'available_search': available_search,
        'available_page_range': available_page_range,
        'available_ellipsis': available_ellipsis,
    }
    return render(request, 'users/admin/curriculum_detail.html', context)


@staff_member_required
@require_POST
def admin_curriculum_approve(request, curriculum_id):
    curriculum = get_object_or_404(
        SpecialtyCurriculum,
        id=curriculum_id
    )

    if curriculum.is_approved or curriculum.is_archived:
        messages.error(
            request,
            'Утвердить можно только черновик учебного плана.'
        )
        return redirect('admin_curriculum_detail', curriculum_id=curriculum.id)

    items = curriculum.items.select_related('plan')

    if not items.exists():
        messages.error(
            request,
            'Нельзя утвердить учебный план без дисциплин.'
        )
        return redirect('admin_curriculum_detail', curriculum_id=curriculum.id)

    if items.exclude(
            plan__is_approved=True,
            plan__is_archived=False
    ).exists():
        messages.error(
            request,
            'Все дисциплины должны быть утверждены и не находиться в архиве.'
        )
        return redirect('admin_curriculum_detail', curriculum_id=curriculum.id)

    curriculum.is_approved = True

    try:
        curriculum.full_clean()
        curriculum.save(update_fields=['is_approved'])
        messages.success(request, 'Учебный план утверждён.')
    except ValidationError as error:
        for message in error.messages:
            messages.error(request, message)

    return redirect('admin_curriculum_detail', curriculum_id=curriculum.id)


@staff_member_required
@require_POST
def admin_curriculum_item_add(request, curriculum_id):
    curriculum = get_object_or_404(
        SpecialtyCurriculum,
        id=curriculum_id
    )

    if curriculum.is_approved or curriculum.is_archived:
        messages.error(
            request,
            'Изменять состав можно только у черновика учебного плана.'
        )
        return redirect('admin_curriculum_detail', curriculum_id=curriculum.id)

    plan = get_object_or_404(
        DisciplinePlan,
        id=request.POST.get('plan_id'),
        is_approved=True,
        is_archived=False
    )

    item = SpecialtyCurriculumItem(
        curriculum=curriculum,
        plan=plan
    )

    try:
        item.full_clean()
        item.save()
        messages.success(request, 'Дисциплина добавлена в учебный план.')
    except ValidationError as error:
        for message in error.messages:
            messages.error(request, message)

    return redirect('admin_curriculum_detail', curriculum_id=curriculum.id)


@staff_member_required
@require_POST
def admin_curriculum_item_delete(request, item_id):
    item = get_object_or_404(
        SpecialtyCurriculumItem.objects.select_related('curriculum'),
        id=item_id
    )
    curriculum = item.curriculum

    if curriculum.is_approved or curriculum.is_archived:
        messages.error(
            request,
            'Изменять состав можно только у черновика учебного плана.'
        )
        return redirect('admin_curriculum_detail', curriculum_id=curriculum.id)

    item.delete()
    messages.success(request, 'Дисциплина удалена из учебного плана.')
    return redirect('admin_curriculum_detail', curriculum_id=curriculum.id)


@staff_member_required
def admin_schedules(request):
    return redirect(f"{reverse('schedule_list')}?manage=1")


def get_schedule_conflicts(
    discipline,
    classroom,
    date,
    lesson_number,
    exclude_schedule_id=None
):
    schedules = Schedule.objects.filter(
        date=date,
        lesson_number=lesson_number
    ).select_related(
        'discipline__plan',
        'discipline__group',
        'discipline__teacher__user',
        'classroom'
    )

    if exclude_schedule_id:
        schedules = schedules.exclude(id=exclude_schedule_id)

    classroom_conflicts = schedules.filter(classroom=classroom)
    teacher_conflicts = schedules.filter(
        discipline__teacher=discipline.teacher
    )

    return classroom_conflicts, teacher_conflicts


@staff_member_required
def admin_schedule_create(request):
    group_id = request.GET.get('group_id')

    if not group_id:
        messages.error(
            request,
            'Сначала выберите группу в расписании.'
        )
        return redirect(
            f"{reverse('schedule_list')}?manage=1"
        )

    initial_date = request.GET.get('date', '')
    initial_lesson_number = request.GET.get('lesson_number', '')

    selected_group = get_object_or_404(
        Group,
        id=group_id
    )

    disciplines = Discipline.objects.select_related(
        'plan',
        'group',
        'teacher__user'
    ).filter(group=selected_group)

    classrooms = Classroom.objects.all()

    return_url = (
        f"{reverse('schedule_list')}?group_id={selected_group.id}"
        f"&date={initial_date}&manage=1"
    )

    context = {
        'disciplines': disciplines,
        'classrooms': classrooms,
        'initial_date': initial_date,
        'initial_lesson_number': initial_lesson_number,
        'return_url': return_url,
        'reset_url': request.get_full_path(),
        'selected_group': selected_group,
    }

    if request.method == 'POST':
        discipline_id = request.POST.get('discipline_id')
        classroom_id = request.POST.get('classroom_id')
        date = request.POST.get('date')
        lesson_number = request.POST.get('lesson_number')

        discipline = get_object_or_404(
            Discipline,
            id=discipline_id,
            group=selected_group
        )

        classroom = get_object_or_404(
            Classroom,
            id=classroom_id
        )

        context['selected_discipline_id'] = discipline.id
        context['selected_classroom_id'] = classroom.id

        context['initial_date'] = date
        context['initial_lesson_number'] = lesson_number

        try:
            lesson_number = int(lesson_number)
            if lesson_number < 1 or lesson_number > 7:
                messages.error(request, 'Номер пары должен быть от 1 до 7.')
                return render(request, 'users/admin/schedule_form.html', context)
        except (ValueError, TypeError):
            messages.error(request, 'Номер пары должен быть числом от 1 до 7.')
            return render(request, 'users/admin/schedule_form.html', context)

        classroom_conflicts, teacher_conflicts = get_schedule_conflicts(
            discipline,
            classroom,
            date,
            lesson_number
        )

        classroom_conflicts = list(classroom_conflicts)
        teacher_conflicts = list(teacher_conflicts)

        ignore_conflicts = request.POST.get('ignore_conflicts') == '1'

        if (classroom_conflicts or teacher_conflicts) and not ignore_conflicts:
            context['classroom_conflicts'] = classroom_conflicts
            context['teacher_conflicts'] = teacher_conflicts

            return render(
                request,
                'users/admin/schedule_form.html',
                context
            )

        schedule = Schedule.objects.create(
            discipline=discipline,
            classroom=classroom,
            date=date,
            lesson_number=lesson_number
        )
        messages.success(request, 'Расписание добавлено.')
        return redirect(
            f"{reverse('schedule_list')}?group_id={schedule.discipline.group_id}&date={date}&manage=1"
        )

    return render(request, 'users/admin/schedule_form.html', context)


@staff_member_required
def admin_schedule_edit(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    has_lesson = Lesson.objects.filter(schedule=schedule).exists()
    return_url = (
        f"{reverse('schedule_list')}?group_id={schedule.discipline.group_id}"
        f"&date={schedule.date.strftime('%Y-%m-%d')}&manage=1"
    )
    disciplines = Discipline.objects.select_related('plan', 'group', 'teacher__user').filter(group=schedule.discipline.group)
    classrooms = Classroom.objects.all()

    context = {
        'schedule': schedule,
        'disciplines': disciplines,
        'classrooms': classrooms,
        'return_url': return_url,
        'reset_url': request.path,
        'has_lesson': has_lesson,
        'selected_group': schedule.discipline.group,
    }

    if request.method == 'POST':
        if has_lesson:
            discipline = schedule.discipline
        else:
            discipline = get_object_or_404(
                Discipline,
                id=request.POST.get('discipline_id'),
                group=schedule.discipline.group
            )

        classroom_id = request.POST.get('classroom_id')
        date = request.POST.get('date')
        lesson_number = request.POST.get('lesson_number')
        classroom = get_object_or_404(
            Classroom,
            id=classroom_id
        )

        context['selected_discipline_id'] = discipline.id
        context['selected_classroom_id'] = classroom.id
        context['initial_date'] = date
        context['initial_lesson_number'] = lesson_number

        try:
            lesson_number = int(lesson_number)
            if lesson_number < 1 or lesson_number > 7:
                messages.error(
                    request,
                    'Номер пары должен быть от 1 до 7.'
                )
                return render(
                    request,
                    'users/admin/schedule_form.html',
                    context
                )
        except (ValueError, TypeError):
            messages.error(request, 'Номер пары должен быть числом от 1 до 7.')
            return render(request, 'users/admin/schedule_form.html', context)

        classroom_conflicts, teacher_conflicts = get_schedule_conflicts(
            discipline,
            classroom,
            date,
            lesson_number,
            exclude_schedule_id=schedule.id
        )

        classroom_conflicts = list(classroom_conflicts)
        teacher_conflicts = list(teacher_conflicts)

        ignore_conflicts = request.POST.get('ignore_conflicts') == '1'

        if (classroom_conflicts or teacher_conflicts) and not ignore_conflicts:
            context['classroom_conflicts'] = classroom_conflicts
            context['teacher_conflicts'] = teacher_conflicts

            return render(
                request,
                'users/admin/schedule_form.html',
                context
            )

        schedule.discipline = discipline
        schedule.classroom = classroom
        schedule.date = date
        schedule.lesson_number = lesson_number
        schedule.save()
        messages.success(request, 'Расписание обновлено.')
        return redirect(
            f"{reverse('schedule_list')}?group_id={schedule.discipline.group_id}&date={date}&manage=1"
        )
    return render(request, 'users/admin/schedule_form.html', context)


@staff_member_required
@require_POST
def admin_schedule_delete(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)

    group_id = schedule.discipline.group_id
    date = schedule.date.strftime('%Y-%m-%d')

    if Lesson.objects.filter(schedule=schedule).exists():
        messages.error(
            request,
            'Нельзя удалить расписание, так как к нему уже прикреплено занятие.'
        )
        return redirect('admin_schedule_edit', schedule_id=schedule.id)

    schedule.delete()
    messages.success(request, 'Расписание удалено.')
    return redirect(
        f"{reverse('schedule_list')}?group_id={group_id}&date={date}&manage=1"
    )


@staff_member_required
def admin_discipline_plans(request):
    show_archived = request.GET.get('show_archived') == '1'
    plans = DisciplinePlan.objects.all().order_by('name')

    if not show_archived:
        plans = plans.filter(is_archived=False)

    search = request.GET.get('search', '')
    if search:
        plans = plans.filter(name__icontains=search)

    paginator = Paginator(plans, 12)
    page_number = request.GET.get('page')
    plans = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(
        plans.number,
        on_each_side=2,
        on_ends=1,
    )

    context = {
        'plans': plans,
        'search': search,
        'page_range': page_range,
        'ellipsis': paginator.ELLIPSIS,
        'show_archived': show_archived,
    }
    return render(request, 'users/admin/discipline_plans.html', context)


@staff_member_required
def admin_discipline_plan_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        total_hours = request.POST.get('total_hours')
        is_approved = request.POST.get('is_approved') == 'on'

        DisciplinePlan.objects.create(
            name=name,
            total_hours=total_hours,
            is_approved=is_approved
        )
        messages.success(request, 'План дисциплины добавлен.')
        return redirect('admin_discipline_plans')

    return render(request, 'users/admin/discipline_plan_form.html')


@staff_member_required
def admin_discipline_plan_edit(request, plan_id):
    plan = get_object_or_404(DisciplinePlan, id=plan_id)

    if plan.is_approved:
        messages.error(request, 'Утверждённый план нельзя изменять.')
        return redirect('admin_discipline_plans')

    if request.method == 'POST':
        plan.name = request.POST.get('name')
        plan.total_hours = request.POST.get('total_hours')
        plan.is_approved = request.POST.get('is_approved') == 'on'
        plan.save()
        messages.success(request, 'План дисциплины обновлён.')
        return redirect('admin_discipline_plans')

    context = {
        'plan': plan,
    }
    return render(request, 'users/admin/discipline_plan_form.html', context)


@staff_member_required
def admin_discipline_plan_delete(request, plan_id):
    plan = get_object_or_404(DisciplinePlan, id=plan_id)

    if plan.is_approved:
        messages.error(request, 'Утверждённый план нельзя удалить.')
        return redirect('admin_discipline_plans')

    if Discipline.objects.filter(plan=plan).exists():
        messages.error(request, 'Нельзя удалить план, так как он используется в дисциплинах.')
        return redirect('admin_discipline_plans')

    plan.delete()
    messages.success(request, 'План дисциплины удалён.')
    return redirect('admin_discipline_plans')


@staff_member_required
@require_POST
def admin_discipline_plan_archive(request, plan_id):
    plan = get_object_or_404(DisciplinePlan, id=plan_id)

    if plan.is_archived:
        plan.is_archived = False
        plan.save(update_fields=['is_archived'])
        messages.success(request, 'План дисциплины восстановлен из архива.')
        return redirect('admin_discipline_plans')

    if not plan.is_approved:
        messages.error(request, 'В архив можно отправить только утверждённый план.')
        return redirect('admin_discipline_plans')

    if Discipline.objects.filter(
        plan=plan,
        semester__status__code='OPEN'
    ).exists():
        messages.error(
            request,
            'План используется в текущем открытом семестре и не может быть архивирован.'
        )
        return redirect('admin_discipline_plans')

    if SpecialtyCurriculumItem.objects.filter(
            plan=plan,
            curriculum__is_approved=True,
            curriculum__is_archived=False
    ).exists():
        messages.error(
            request,
            'План входит в утверждённый учебный план специальности и не может быть архивирован.'
        )
        return redirect('admin_discipline_plans')

    plan.is_archived = True
    plan.save(update_fields=['is_archived'])
    messages.success(request, 'План дисциплины отправлен в архив.')
    return redirect('admin_discipline_plans')


@staff_member_required
def admin_disciplines(request):
    disciplines = Discipline.objects.select_related(
        'plan',
        'group',
        'teacher__user',
    ).order_by(
        'plan__name',
        'group__name',
    )

    search = request.GET.get('search', '')
    if search:
        disciplines = disciplines.filter(
            Q(plan__name__icontains=search) |
            Q(group__name__icontains=search) |
            Q(teacher__user__last_name__icontains=search) |
            Q(teacher__user__first_name__icontains=search)
        )

    paginator = Paginator(disciplines, 12)
    page_number = request.GET.get('page')
    disciplines = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(
        disciplines.number,
        on_each_side=2,
        on_ends=1,
    )

    context = {
        'disciplines': disciplines,
        'search': search,
        'page_range': page_range,
        'ellipsis': paginator.ELLIPSIS,
    }
    return render(request, 'users/admin/disciplines.html', context)


@staff_member_required
def admin_discipline_create(request):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        group_id = request.POST.get('group_id')
        teacher_id = request.POST.get('teacher_id')

        Discipline.objects.create(
            plan_id=plan_id,
            group_id=group_id,
            teacher_id=teacher_id
        )
        messages.success(request, 'Дисциплина добавлена.')
        return redirect('admin_disciplines')

    plans = DisciplinePlan.objects.filter(is_approved=True, is_archived=False)
    groups = Group.objects.all()
    teachers = Teacher.objects.select_related('user').all()

    context = {
        'plans': plans,
        'groups': groups,
        'teachers': teachers,
    }
    return render(request, 'users/admin/discipline_form.html', context)


@staff_member_required
def admin_discipline_edit(request, discipline_id):
    discipline = get_object_or_404(Discipline, id=discipline_id)

    if request.method == 'POST':
        discipline.plan_id = request.POST.get('plan_id')
        discipline.group_id = request.POST.get('group_id')
        discipline.teacher_id = request.POST.get('teacher_id')
        discipline.save()
        messages.success(request, 'Дисциплина обновлена.')
        return redirect('admin_disciplines')

    plans = DisciplinePlan.objects.filter(Q(is_approved=True, is_archived=False) | Q(id=discipline.plan_id))
    groups = Group.objects.all()
    teachers = Teacher.objects.select_related('user').all()

    context = {
        'discipline': discipline,
        'plans': plans,
        'groups': groups,
        'teachers': teachers,
    }
    return render(request, 'users/admin/discipline_form.html', context)


@staff_member_required
def admin_discipline_delete(request, discipline_id):
    discipline = get_object_or_404(Discipline, id=discipline_id)

    if Schedule.objects.filter(discipline=discipline).exists():
        messages.error(request, 'Нельзя удалить дисциплину, так как она используется в расписании.')
        return redirect('admin_disciplines')

    discipline.delete()
    messages.success(request, 'Дисциплина удалена.')
    return redirect('admin_disciplines')