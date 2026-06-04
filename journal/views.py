from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib import messages
from .models import (
    Teacher, Department, Group, Discipline,
    Specialty, Schedule, ContactMessage, MessageStatus,
    DisciplinePlan
)
from django.db.models import Q

def home(request):
    return render(request, 'journal/home.html')


def teachers_list(request):
    teachers = Teacher.objects.select_related('user').all()

    search = request.GET.get('search', '')
    if search:
        teachers = teachers.filter(
            Q(user__last_name__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__patronymic__icontains=search)
        )

    context = {
        'teachers': teachers,
        'search': search,
    }
    return render(request, 'journal/teachers.html', context)


def departments_list(request):
    departments = Department.objects.all()
    return render(request, 'journal/departments.html', {'departments': departments})


def groups_list(request):
    groups = Group.objects.select_related('specialty__department').all()

    search = request.GET.get('search', '')
    if search:
        groups = groups.filter(
            Q(name__icontains=search) |
            Q(year__icontains=search) |
            Q(specialty__department__name__icontains=search) |
            Q(specialty__name__icontains=search)
        )

    context = {
        'groups': groups,
        'search': search,
    }
    return render(request, 'journal/groups.html', context)


def disciplines_list(request):
    disciplines = Discipline.objects.select_related('plan', 'group', 'teacher__user').all()

    search = request.GET.get('search', '')
    if search:
        disciplines = disciplines.filter(
            Q(plan__name__icontains=search) |
            Q(group__name__icontains=search) |
            Q(teacher__user__last_name__icontains=search) |
            Q(teacher__user__first_name__icontains=search)
        )

    context = {
        'disciplines': disciplines,
        'search': search,
    }
    return render(request, 'journal/disciplines.html', context)


def discipline_plans_list(request):
    plans = DisciplinePlan.objects.all().order_by('name')

    search = request.GET.get('search', '')
    if search:
        plans = plans.filter(name__icontains=search)

    context = {
        'plans': plans,
        'search': search,
    }
    return render(request, 'journal/discipline_plans.html', context)


def specialties_list(request):
    specialties = Specialty.objects.select_related('department').all()

    search = request.GET.get('search', '')
    if search:
        specialties = specialties.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(qualification__icontains=search) |
            Q(department__name__icontains=search)
        )

    context = {
        'specialties': specialties,
        'search': search,
    }
    return render(request, 'journal/specialties.html', context)


def schedule_list(request):
    groups = Group.objects.all()
    group_id = request.GET.get('group_id')
    selected_group = None

    if group_id:
        selected_group = get_object_or_404(Group, id=group_id)

    week_offset = int(request.GET.get('week_offset', 0))

    week_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

    today = timezone.now().date()
    target_date = today + timedelta(weeks=week_offset)
    monday = target_date - timedelta(days=target_date.weekday())
    week_dates = [monday + timedelta(days=i) for i in range(7)]

    today_index = -1
    if week_offset == 0:
        for i, date in enumerate(week_dates):
            if date == today:
                today_index = i
                break

    week_range = f"{monday.strftime('%d.%m.%Y')} — {(monday + timedelta(days=6)).strftime('%d.%m.%Y')}"
    week_schedule = [(week_days[i], week_dates[i]) for i in range(7)]
    lesson_numbers = list(range(1, 8))

    schedule_grid = {}

    if selected_group:
        schedules = Schedule.objects.filter(
            discipline__group=selected_group,
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

    context = {
        'groups': groups,
        'selected_group': selected_group,
        'week_schedule': week_schedule,
        'lesson_numbers': lesson_numbers,
        'schedule_grid': schedule_grid,
        'range_0_6': range(7),
        'today_index': today_index,
        'week_offset': week_offset,
        'week_range': week_range,
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