from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    Department, Group, Teacher, Student, DisciplinePlan, Discipline,
    Classroom, Schedule, Lesson, LessonType, Task, LessonFile,
    Grade, Attendance, AttendanceType, ContactMessage, MessageStatus
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address')
    search_fields = ('name',)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'year', 'department')
    list_filter = ('year', 'department')
    search_fields = ('name',)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_full_name')
    search_fields = ('user__username', 'user__last_name', 'user__first_name')

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    get_full_name.short_description = 'ФИО'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'special_number', 'user', 'group')
    list_filter = ('group',)
    search_fields = ('special_number', 'user__last_name', 'user__first_name')


@admin.register(DisciplinePlan)
class DisciplinePlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'total_hours')
    search_fields = ('name',)


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ('id', 'plan', 'group', 'teacher')
    list_filter = ('group', 'teacher')
    search_fields = ('plan__name', 'group__name')


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'department')
    list_filter = ('department',)
    search_fields = ('number',)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'lesson_number', 'discipline', 'classroom')
    list_filter = ('date', 'lesson_number', 'discipline__group')
    search_fields = ('discipline__plan__name',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', 'schedule', 'topic', 'lesson_type', 'hours')
    list_filter = ('lesson_type', 'schedule__discipline__group')
    search_fields = ('topic',)


@admin.register(LessonType)
class LessonTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'lesson')
    list_filter = ('lesson__schedule__discipline__group',)
    search_fields = ('name',)


@admin.register(LessonFile)
class LessonFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'lesson', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('name',)


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'value', 'task', 'student', 'created_at')
    list_filter = ('value', 'created_at', 'task__lesson__schedule__discipline__group')
    search_fields = ('student__user__last_name',)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'lesson', 'student', 'attendance_type')
    list_filter = ('attendance_type', 'lesson__schedule__discipline__group')
    search_fields = ('student__user__last_name',)


@admin.register(AttendanceType)
class AttendanceTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'created_at', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email')


@admin.register(MessageStatus)
class MessageStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)