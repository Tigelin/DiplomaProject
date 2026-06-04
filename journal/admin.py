from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import (
    Department, Group, Teacher, Student, DisciplinePlan, Discipline,
    Classroom, Schedule, Lesson, LessonType, Task, LessonFile,
    Grade, Attendance, AttendanceType, ContactMessage, MessageStatus,
    Specialty
)


class SaveAndAddAnotherMixin:
    def response_add(self, request, obj, post_url_continue=None):
        if '_save_and_add_another_empty' in request.POST:
            return HttpResponseRedirect(
                reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_add'))
        if '_save_and_add_another_filled' in request.POST:
            return self._redirect_to_add_with_data(request, obj)
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if '_save_and_add_another_empty' in request.POST:
            return HttpResponseRedirect(
                reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_add'))
        if '_save_and_add_another_filled' in request.POST:
            return self._redirect_to_add_with_data(request, obj)
        return super().response_change(request, obj)

    def _redirect_to_add_with_data(self, request, obj):
        return HttpResponseRedirect(self.get_add_url_with_data(request, obj))

    def get_add_url_with_data(self, request, obj):
        return reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_add')


@admin.register(Department)
class DepartmentAdmin(SaveAndAddAnotherMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'address')
    search_fields = ('name',)

    def get_add_url_with_data(self, request, obj):
        return f"{reverse('admin:journal_department_add')}?name={obj.name}&address={obj.address}"

    def get_changeform_initial_data(self, request):
        return {
            'name': request.GET.get('name'),
            'address': request.GET.get('address'),
        }


@admin.register(Group)
class GroupAdmin(SaveAndAddAnotherMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'year', 'specialty', 'get_department')
    list_filter = ('year', 'specialty')
    search_fields = ('name',)

    def get_department(self, obj):
        return obj.specialty.department.name
    get_department.short_description = 'Отделение'

    def get_add_url_with_data(self, request, obj):
        return f"{reverse('admin:journal_group_add')}?name={obj.name}&year={obj.year}&specialty={obj.specialty.id}"

    def get_changeform_initial_data(self, request):
        return {
            'name': request.GET.get('name'),
            'year': request.GET.get('year'),
            'specialty': request.GET.get('specialty'),
        }


@admin.register(Teacher)
class TeacherAdmin(SaveAndAddAnotherMixin, admin.ModelAdmin):
    list_display = ('id', 'user', 'get_full_name')
    search_fields = ('user__username', 'user__last_name', 'user__first_name')

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    get_full_name.short_description = 'ФИО'

    def get_add_url_with_data(self, request, obj):
        return f"{reverse('admin:journal_teacher_add')}?user={obj.user.id}"

    def get_changeform_initial_data(self, request):
        return {
            'user': request.GET.get('user'),
        }


@admin.register(Student)
class StudentAdmin(SaveAndAddAnotherMixin, admin.ModelAdmin):
    list_display = ('id', 'special_number', 'user', 'group')
    list_filter = ('group',)
    search_fields = ('special_number', 'user__last_name', 'user__first_name')

    def get_add_url_with_data(self, request, obj):
        return f"{reverse('admin:journal_student_add')}?special_number={obj.special_number}&user={obj.user.id}&group={obj.group.id}"

    def get_changeform_initial_data(self, request):
        return {
            'special_number': request.GET.get('special_number'),
            'user': request.GET.get('user'),
            'group': request.GET.get('group'),
        }


@admin.register(DisciplinePlan)
class DisciplinePlanAdmin(SaveAndAddAnotherMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'total_hours')
    search_fields = ('name',)

    def get_add_url_with_data(self, request, obj):
        return f"{reverse('admin:journal_disciplineplan_add')}?name={obj.name}&total_hours={obj.total_hours}"

    def get_changeform_initial_data(self, request):
        return {
            'name': request.GET.get('name'),
            'total_hours': request.GET.get('total_hours'),
        }


@admin.register(Discipline)
class DisciplineAdmin(SaveAndAddAnotherMixin, admin.ModelAdmin):
    list_display = ('id', 'plan', 'group', 'teacher')
    list_filter = ('group', 'teacher')
    search_fields = ('plan__name', 'group__name')

    def get_add_url_with_data(self, request, obj):
        return f"{reverse('admin:journal_discipline_add')}?plan={obj.plan.id}&group={obj.group.id}&teacher={obj.teacher.id}"

    def get_changeform_initial_data(self, request):
        return {
            'plan': request.GET.get('plan'),
            'group': request.GET.get('group'),
            'teacher': request.GET.get('teacher'),
        }


@admin.register(Classroom)
class ClassroomAdmin(SaveAndAddAnotherMixin, admin.ModelAdmin):
    list_display = ('id', 'number', 'department')
    list_filter = ('department',)
    search_fields = ('number',)

    def get_add_url_with_data(self, request, obj):
        return f"{reverse('admin:journal_classroom_add')}?number={obj.number}&department={obj.department.id}"

    def get_changeform_initial_data(self, request):
        return {
            'number': request.GET.get('number'),
            'department': request.GET.get('department'),
        }


@admin.register(Schedule)
class ScheduleAdmin(SaveAndAddAnotherMixin, admin.ModelAdmin):
    list_display = ('id', 'date', 'lesson_number', 'discipline', 'classroom')
    list_filter = ('date', 'lesson_number', 'discipline__group')
    search_fields = ('discipline__plan__name',)

    def get_add_url_with_data(self, request, obj):
        return f"{reverse('admin:journal_schedule_add')}?discipline={obj.discipline.id}&classroom={obj.classroom.id}&date={obj.date}&lesson_number={obj.lesson_number}"

    def get_changeform_initial_data(self, request):
        return {
            'discipline': request.GET.get('discipline'),
            'classroom': request.GET.get('classroom'),
            'date': request.GET.get('date'),
            'lesson_number': request.GET.get('lesson_number'),
        }


@admin.register(Lesson)
class LessonAdmin(SaveAndAddAnotherMixin, admin.ModelAdmin):
    list_display = ('id', 'schedule', 'topic', 'lesson_type', 'hours')
    list_filter = ('lesson_type', 'schedule__discipline__group')
    search_fields = ('topic',)

    def get_add_url_with_data(self, request, obj):
        return f"{reverse('admin:journal_lesson_add')}?schedule={obj.schedule.id}&topic={obj.topic}&lesson_type={obj.lesson_type.id}&hours={obj.hours}"

    def get_changeform_initial_data(self, request):
        return {
            'schedule': request.GET.get('schedule'),
            'topic': request.GET.get('topic'),
            'lesson_type': request.GET.get('lesson_type'),
            'hours': request.GET.get('hours'),
        }


@admin.register(LessonType)
class LessonTypeAdmin(SaveAndAddAnotherMixin, admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

    def get_add_url_with_data(self, request, obj):
        return f"{reverse('admin:journal_lessontype_add')}?name={obj.name}"

    def get_changeform_initial_data(self, request):
        return {
            'name': request.GET.get('name'),
        }


@admin.register(Task)
class TaskAdmin(SaveAndAddAnotherMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'lesson')
    list_filter = ('lesson__schedule__discipline__group',)
    search_fields = ('name',)

    def get_add_url_with_data(self, request, obj):
        return f"{reverse('admin:journal_task_add')}?name={obj.name}&lesson={obj.lesson.id}"

    def get_changeform_initial_data(self, request):
        return {
            'name': request.GET.get('name'),
            'lesson': request.GET.get('lesson'),
        }


@admin.register(LessonFile)
class LessonFileAdmin(SaveAndAddAnotherMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'lesson', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('name',)

    def get_add_url_with_data(self, request, obj):
        return f"{reverse('admin:journal_lessonfile_add')}?name={obj.name}&lesson={obj.lesson.id}"

    def get_changeform_initial_data(self, request):
        return {
            'name': request.GET.get('name'),
            'lesson': request.GET.get('lesson'),
        }


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'value', 'task', 'student', 'created_at')
    list_filter = ('value', 'created_at', 'task__lesson__schedule__discipline__group')
    search_fields = ('student__user__last_name',)
    actions = ['set_grade_5', 'set_grade_4', 'set_grade_3', 'set_grade_2', 'set_grade_1', 'delete_grades']

    def set_grade_5(self, request, queryset):
        updated = queryset.update(value=5)
        self.message_user(request, f'У {updated} оценок установлено значение 5.')

    set_grade_5.short_description = 'Установить оценку 5'

    def set_grade_4(self, request, queryset):
        updated = queryset.update(value=4)
        self.message_user(request, f'У {updated} оценок установлено значение 4.')

    set_grade_4.short_description = 'Установить оценку 4'

    def set_grade_3(self, request, queryset):
        updated = queryset.update(value=3)
        self.message_user(request, f'У {updated} оценок установлено значение 3.')

    set_grade_3.short_description = 'Установить оценку 3'

    def set_grade_2(self, request, queryset):
        updated = queryset.update(value=2)
        self.message_user(request, f'У {updated} оценок установлено значение 2.')

    set_grade_2.short_description = 'Установить оценку 2'

    def set_grade_1(self, request, queryset):
        updated = queryset.update(value=1)
        self.message_user(request, f'У {updated} оценок установлено значение 1.')

    set_grade_1.short_description = 'Установить оценку 1'

    def delete_grades(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'Удалено {count} оценок.')

    delete_grades.short_description = 'Удалить выбранные оценки'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'lesson', 'student', 'attendance_type')
    list_filter = ('attendance_type', 'lesson__schedule__discipline__group')
    search_fields = ('student__user__last_name',)
    actions = ['set_present', 'set_late', 'set_sick', 'set_excused', 'set_absent']

    def set_present(self, request, queryset):
        attendance_type, _ = AttendanceType.objects.get_or_create(name='Присутствовал')
        updated = queryset.update(attendance_type=attendance_type)
        self.message_user(request, f'У {updated} записей установлено "Присутствовал".')

    set_present.short_description = 'Отметить как присутствовал'

    def set_late(self, request, queryset):
        attendance_type, _ = AttendanceType.objects.get_or_create(name='Опоздал')
        updated = queryset.update(attendance_type=attendance_type)
        self.message_user(request, f'У {updated} записей установлено "Опоздал".')

    set_late.short_description = 'Отметить как опоздал'

    def set_sick(self, request, queryset):
        attendance_type, _ = AttendanceType.objects.get_or_create(name='Отсутствовал по болезни')
        updated = queryset.update(attendance_type=attendance_type)
        self.message_user(request, f'У {updated} записей установлено "Отсутствовал по болезни".')

    set_sick.short_description = 'Отметить как больной'

    def set_excused(self, request, queryset):
        attendance_type, _ = AttendanceType.objects.get_or_create(name='Отсутствовал по уважительной причине')
        updated = queryset.update(attendance_type=attendance_type)
        self.message_user(request, f'У {updated} записей установлено "Отсутствовал по уважительной причине".')

    set_excused.short_description = 'Отметить как отсутствие по уважительной причине'

    def set_absent(self, request, queryset):
        attendance_type, _ = AttendanceType.objects.get_or_create(name='Отсутствовал без причины')
        updated = queryset.update(attendance_type=attendance_type)
        self.message_user(request, f'У {updated} записей установлено "Отсутствовал без причины".')

    set_absent.short_description = 'Отметить как отсутствие без причины'


@admin.register(AttendanceType)
class AttendanceTypeAdmin(SaveAndAddAnotherMixin, admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

    def get_add_url_with_data(self, request, obj):
        return f"{reverse('admin:journal_attendancetype_add')}?name={obj.name}"

    def get_changeform_initial_data(self, request):
        return {
            'name': request.GET.get('name'),
        }


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'created_at', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email')
    actions = ['mark_as_new', 'mark_as_processing', 'mark_as_processed', 'mark_as_answered', 'delete_messages']

    def mark_as_new(self, request, queryset):
        status, _ = MessageStatus.objects.get_or_create(name='Новое')
        updated = queryset.update(status=status)
        self.message_user(request, f'{updated} сообщений отмечено как "Новое".')

    mark_as_new.short_description = 'Отметить как "Новое"'

    def mark_as_processing(self, request, queryset):
        status, _ = MessageStatus.objects.get_or_create(name='В обработке')
        updated = queryset.update(status=status)
        self.message_user(request, f'{updated} сообщений отмечено как "В обработке".')

    mark_as_processing.short_description = 'Отметить как "В обработке"'

    def mark_as_processed(self, request, queryset):
        status, _ = MessageStatus.objects.get_or_create(name='Обработано')
        updated = queryset.update(status=status)
        self.message_user(request, f'{updated} сообщений отмечено как "Обработано".')

    mark_as_processed.short_description = 'Отметить как "Обработано"'

    def mark_as_answered(self, request, queryset):
        status, _ = MessageStatus.objects.get_or_create(name='Отвечено')
        updated = queryset.update(status=status)
        self.message_user(request, f'{updated} сообщений отмечено как "Отвечено".')

    mark_as_answered.short_description = 'Отметить как "Отвечено"'

    def delete_messages(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'Удалено {count} сообщений.')

    delete_messages.short_description = 'Удалить выбранные сообщения'


@admin.register(MessageStatus)
class MessageStatusAdmin(SaveAndAddAnotherMixin, admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

    def get_add_url_with_data(self, request, obj):
        return f"{reverse('admin:journal_messagestatus_add')}?name={obj.name}"

    def get_changeform_initial_data(self, request):
        return {
            'name': request.GET.get('name'),
        }


@admin.register(Specialty)
class SpecialtyAdmin(SaveAndAddAnotherMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'qualification', 'department')
    list_filter = ('department',)
    search_fields = ('name', 'code', 'qualification')