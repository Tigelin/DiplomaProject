from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib import messages
from .models import (
    Teacher, Department, Group, Discipline,
    Specialty, Schedule, ContactMessage, MessageStatus,
    DisciplinePlan, AcademicSemester
)
from django.db.models import Q
from django.core.paginator import Paginator

def home(request):
    return render(request, 'journal/home.html')


def teachers_list(request):
    teachers = Teacher.objects.select_related('user').order_by(
        'user__last_name',
        'user__first_name',
        'user__patronymic',
    )

    search = request.GET.get('search', '')
    if search:
        teachers = teachers.filter(
            Q(user__last_name__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__patronymic__icontains=search)
        )

    paginator = Paginator(teachers, 12)
    page_number = request.GET.get('page')
    teachers = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(
        teachers.number,
        on_each_side=2,
        on_ends=1,
    )

    context = {
        'teachers': teachers,
        'search': search,
        'page_range': page_range,
        'ellipsis': paginator.ELLIPSIS,
    }
    return render(request, 'journal/teachers.html', context)


def departments_list(request):
    departments = Department.objects.all()
    return render(request, 'journal/departments.html', {'departments': departments})


def groups_list(request):
    semesters = AcademicSemester.objects.exclude(
        status__code='DRAFT'
    ).select_related('status').order_by('-start_date')

    semester_id = request.GET.get('semester_id')
    if semester_id:
        selected_semester = get_object_or_404(
            semesters,
            id=semester_id
        )
    else:
        selected_semester = semesters.first()

    groups = []
    search = request.GET.get('search', '')

    if selected_semester:
        available_groups = Group.objects.select_related(
            'specialty__department',
            'number_set',
        )

        for group in available_groups:
            study_semester = group.get_study_semester(selected_semester)

            if (
                study_semester < 1
                or study_semester > group.specialty.duration_semesters
            ):
                continue

            group.display_name = group.get_display_name(selected_semester)

            if search:
                search_value = search.lower()

                if not (
                    search_value in group.display_name.lower()
                    or search_value in str(group.year)
                    or search_value in group.specialty.name.lower()
                    or search_value in group.specialty.department.name.lower()
                ):
                    continue

            groups.append(group)

        groups.sort(
            key=lambda group: (
                group.specialty.name,
                group.display_name,
                group.year,
            )
        )

    paginator = Paginator(groups, 15)
    page_number = request.GET.get('page')
    groups = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(
        groups.number,
        on_each_side=2,
        on_ends=1,
    )

    context = {
        'groups': groups,
        'search': search,
        'page_range': page_range,
        'ellipsis': paginator.ELLIPSIS,
        'semesters': semesters,
        'selected_semester': selected_semester,
    }
    return render(request, 'journal/groups.html', context)


def disciplines_list(request):
    semesters = AcademicSemester.objects.exclude(
        status__code='DRAFT'
    ).select_related('status').order_by('-start_date')

    semester_id = request.GET.get('semester_id')
    if semester_id:
        selected_semester = get_object_or_404(
            semesters,
            id=semester_id
        )
    else:
        selected_semester = semesters.first()

    disciplines = []
    search = request.GET.get('search', '')

    if selected_semester:
        available_disciplines = Discipline.objects.filter(
            semester=selected_semester
        ).select_related(
            'plan',
            'group__number_set',
            'teacher__user',
        )

        group_names = {}
        search_value = search.lower()

        for discipline in available_disciplines:
            if discipline.group_id not in group_names:
                group_names[discipline.group_id] = (
                    discipline.group.get_display_name(selected_semester)
                )

            discipline.group.display_name = group_names[
                discipline.group_id
            ]

            if search:
                if not (
                    search_value in discipline.plan.name.lower()
                    or search_value in discipline.group.display_name.lower()
                    or search_value in discipline.teacher.user.get_full_name().lower()
                ):
                    continue

            disciplines.append(discipline)

        disciplines.sort(
            key=lambda discipline: (
                discipline.plan.name,
                discipline.group.display_name,
            )
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
        'disciplines': disciplines,
        'search': search,
        'page_range': page_range,
        'ellipsis': paginator.ELLIPSIS,
        'semesters': semesters,
        'selected_semester': selected_semester,
    }
    return render(request, 'journal/disciplines.html', context)


def discipline_plans_list(request):
    plans = DisciplinePlan.objects.filter(
        is_approved=True,
        is_archived=False,
    ).order_by('name')

    search = request.GET.get('search', '')
    if search:
        plans = plans.filter(name__icontains=search)

    paginator = Paginator(plans, 15)
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
    }
    return render(request, 'journal/discipline_plans.html', context)


def specialties_list(request):
    specialties = Specialty.objects.select_related('department').order_by(
        'name',
        'code',
    )

    search = request.GET.get('search', '')
    if search:
        specialties = specialties.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(qualification__icontains=search) |
            Q(department__name__icontains=search)
        )

    paginator = Paginator(specialties, 6)
    page_number = request.GET.get('page')
    specialties = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(
        specialties.number,
        on_each_side=2,
        on_ends=1,
    )

    context = {
        'specialties': specialties,
        'search': search,
        'page_range': page_range,
        'ellipsis': paginator.ELLIPSIS,
    }
    return render(request, 'journal/specialties.html', context)


def schedule_list(request):
    semesters = AcademicSemester.objects.exclude(
        status__code='DRAFT'
    ).select_related('status').order_by('-start_date')

    semester_id = request.GET.get('semester_id')
    if semester_id:
        selected_semester = get_object_or_404(
            semesters,
            id=semester_id
        )
    else:
        selected_semester = semesters.first()

    groups = Group.objects.none()
    selected_group = None

    if selected_semester:
        groups = Group.objects.filter(
            discipline__semester=selected_semester
        ).select_related(
            'specialty'
        ).distinct()

    group_id = request.GET.get('group_id')
    if group_id and selected_semester:
        selected_group = get_object_or_404(
            groups,
            id=group_id
        )

    groups = list(groups)
    for group in groups:
        group.display_name = group.get_display_name(selected_semester)

    groups.sort(
        key=lambda group: (
            group.specialty.name,
            group.display_name,
            group.year,
        )
    )

    if selected_group:
        selected_group.display_name = selected_group.get_display_name(
            selected_semester
        )

    try:
        week_offset = int(request.GET.get('week_offset', 0))
    except (ValueError, TypeError):
        week_offset = 0

    selected_date = request.GET.get('date', '')
    week_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

    today = timezone.localdate()
    target_date = today
    first_monday = None
    last_monday = None
    last_sunday = None

    if selected_semester:
        first_monday = (
            selected_semester.start_date -
            timedelta(days=selected_semester.start_date.weekday())
        )
        last_monday = (
            selected_semester.end_date -
            timedelta(days=selected_semester.end_date.weekday())
        )
        last_sunday = last_monday + timedelta(days=6)

        if today < first_monday or today > last_sunday:
            target_date = selected_semester.start_date

    if selected_date:
        try:
            target_date = datetime.strptime(
                selected_date,
                '%Y-%m-%d'
            ).date()

            if selected_semester:
                if target_date < selected_semester.start_date:
                    target_date = selected_semester.start_date
                    selected_date = selected_semester.start_date.strftime(
                        '%Y-%m-%d'
                    )
                elif target_date > selected_semester.end_date:
                    target_date = selected_semester.end_date
                    selected_date = selected_semester.end_date.strftime(
                        '%Y-%m-%d'
                    )
        except ValueError:
            selected_date = ''

    base_monday = target_date - timedelta(days=target_date.weekday())

    if selected_semester:
        minimum_week_offset = (
            first_monday - base_monday
        ).days // 7
        maximum_week_offset = (
            last_monday - base_monday
        ).days // 7
        week_offset = max(
            minimum_week_offset,
            min(week_offset, maximum_week_offset)
        )
    else:
        week_offset = 0

    monday = base_monday + timedelta(weeks=week_offset)
    week_dates = [monday + timedelta(days=i) for i in range(7)]

    current_monday = today - timedelta(days=today.weekday())
    is_current_week = monday == current_monday

    today_index = -1
    for i, date in enumerate(week_dates):
        if date == today:
            today_index = i
            break

    week_range = f"{monday.strftime('%d.%m.%Y')} — {(monday + timedelta(days=6)).strftime('%d.%m.%Y')}"
    week_schedule = [(week_days[i], week_dates[i]) for i in range(7)]
    lesson_numbers = list(range(1, 8))

    manage_mode = request.GET.get('manage') == '1' and request.user.is_staff
    schedule_grid = {}
    schedule_creation_days = []

    if selected_group and selected_semester:
        schedules = Schedule.objects.filter(
            discipline__group=selected_group,
            discipline__semester=selected_semester,
            date__gte=monday,
            date__lte=monday + timedelta(days=6)
        ).select_related(
            'discipline__plan',
            'discipline__teacher__user',
            'classroom'
        )

        for s in schedules:
            weekday = s.date.weekday()
            if weekday not in schedule_grid:
                schedule_grid[weekday] = {}
            schedule_grid[weekday][s.lesson_number] = s

        if (
            manage_mode and
            selected_semester.status.code == 'OPEN' and
            Discipline.objects.filter(
                group=selected_group,
                semester=selected_semester,
                is_confirmed=True
            ).exists()
        ):
            for i, date in enumerate(week_dates):
                if (
                    selected_semester.start_date <= date <=
                    selected_semester.end_date
                ):
                    schedule_creation_days.append(i)

    context = {
        'semesters': semesters,
        'selected_semester': selected_semester,
        'groups': groups,
        'selected_group': selected_group,
        'week_schedule': week_schedule,
        'lesson_numbers': lesson_numbers,
        'schedule_grid': schedule_grid,
        'schedule_creation_days': schedule_creation_days,
        'range_0_6': range(7),
        'today_index': today_index,
        'week_offset': week_offset,
        'week_range': week_range,
        'selected_date': selected_date,
        'is_current_week': is_current_week,
        'manage_mode': manage_mode,
        'has_previous_week': (
            selected_semester and monday > first_monday
        ),
        'has_next_week': (
            selected_semester and monday < last_monday
        ),
        'return_to_first_week': (
            selected_semester and
            (today < first_monday or today > last_sunday)
        ),
        'week_dates_by_index': {
            i: date for i, date in enumerate(week_dates)
        },
    }
    return render(request, 'journal/schedule.html', context)


def about(request):
    return render(request, 'journal/about.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message_text = request.POST.get('message')

        new_status, _ = MessageStatus.objects.get_or_create(name='Новое')

        ContactMessage.objects.create(
            name=name,
            email=email,
            message=message_text,
            status=new_status
        )
        messages.success(request, 'Ваше сообщение отправлено! Мы свяжемся с вами.')
        return redirect('contact')

    return render(request, 'journal/contact.html')
