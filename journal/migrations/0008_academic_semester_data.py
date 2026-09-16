from datetime import date

from django.db import migrations


def migrate_academic_data(apps, schema_editor):
    AcademicSemesterStatus = apps.get_model('journal', 'AcademicSemesterStatus')
    AcademicSemester = apps.get_model('journal', 'AcademicSemester')
    Schedule = apps.get_model('journal', 'Schedule')
    Lesson = apps.get_model('journal', 'Lesson')
    Task = apps.get_model('journal', 'Task')
    Grade = apps.get_model('journal', 'Grade')
    Attendance = apps.get_model('journal', 'Attendance')
    LessonFile = apps.get_model('journal', 'LessonFile')
    DisciplinePlan = apps.get_model('journal', 'DisciplinePlan')
    Discipline = apps.get_model('journal', 'Discipline')
    Specialty = apps.get_model('journal', 'Specialty')
    Group = apps.get_model('journal', 'Group')
    GroupNumberSet = apps.get_model('journal', 'GroupNumberSet')
    GroupNumberEntry = apps.get_model('journal', 'GroupNumberEntry')
    SpecialtyCurriculumItem = apps.get_model('journal', 'SpecialtyCurriculumItem')
    Student = apps.get_model('journal', 'Student')
    StudentGroupMembership = apps.get_model('journal', 'StudentGroupMembership')

    september_schedules = Schedule.objects.filter(date__year=2026, date__month=9)

    actual_counts = {
        'schedules': september_schedules.count(),
        'lessons': Lesson.objects.filter(schedule__in=september_schedules).count(),
        'tasks': Task.objects.filter(lesson__schedule__in=september_schedules).count(),
        'grades': Grade.objects.filter(task__lesson__schedule__in=september_schedules).count(),
        'attendance': Attendance.objects.filter(lesson__schedule__in=september_schedules).count(),
        'lesson_files': LessonFile.objects.filter(lesson__schedule__in=september_schedules).count(),
    }

    expected_counts = {
        'schedules': 24,
        'lessons': 5,
        'tasks': 8,
        'grades': 207,
        'attendance': 135,
        'lesson_files': 1,
    }

    if actual_counts != expected_counts:
        raise RuntimeError(
            f"Unexpected September data counts: {actual_counts}"
        )

    september_schedules.delete()

    draft_status = AcademicSemesterStatus.objects.create(
        code='DRAFT',
        name='Черновик',
    )
    closed_status = AcademicSemesterStatus.objects.create(
        code='CLOSED',
        name='Закрыт',
    )
    AcademicSemesterStatus.objects.create(
        code='OPEN',
        name='Открыт',
    )

    spring_semester = AcademicSemester.objects.create(
        start_year=2025,
        is_first_semester=False,
        start_date=date(2026, 1, 12),
        end_date=date(2026, 6, 27),
        status=closed_status,
    )
    AcademicSemester.objects.create(
        start_year=2026,
        is_first_semester=True,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 12, 30),
        status=draft_status,
    )

    DisciplinePlan.objects.update(is_approved=True)
    Discipline.objects.update(
        semester=spring_semester,
        is_confirmed=True,
    )

    for specialty in Specialty.objects.all():
        number_set = GroupNumberSet.objects.create(
            name='Основной комплект',
            specialty=specialty,
        )
        used_courses = set()

        for group in Group.objects.filter(specialty=specialty):
            study_semester = (
                (spring_semester.start_year - group.year) * 2 + 2
            )
            course = (study_semester + 1) // 2

            if study_semester < 1 or study_semester > specialty.duration_semesters:
                raise RuntimeError(
                    f"Invalid study semester for group {group.id}: "
                    f"{study_semester}"
                )

            if course in used_courses:
                raise RuntimeError(
                    f"Several groups use course {course} "
                    f"for specialty {specialty.id}"
                )

            used_courses.add(course)

            GroupNumberEntry.objects.create(
                number_set=number_set,
                course=course,
                name=group.name,
            )

            group.number_set = number_set
            group.is_graduated = (
                study_semester == specialty.duration_semesters
            )
            group.save(update_fields=['number_set', 'is_graduated'])

    curriculum_items = set()

    for discipline in Discipline.objects.select_related(
        'group__specialty'
    ):
        group = discipline.group
        specialty = group.specialty
        study_semester = (
            (spring_semester.start_year - group.year) * 2 + 2
        )

        if study_semester < 1 or study_semester > specialty.duration_semesters:
            raise RuntimeError(
                f"Invalid study semester for discipline {discipline.id}: "
                f"{study_semester}"
            )

        item = (
            specialty.id,
            study_semester,
            discipline.plan_id,
        )

        if item not in curriculum_items:
            SpecialtyCurriculumItem.objects.create(
                specialty=specialty,
                study_semester=study_semester,
                plan_id=discipline.plan_id,
            )
            curriculum_items.add(item)

    for student in Student.objects.select_related('group'):
        if student.group is None:
            raise RuntimeError(
                f"Student {student.id} has no group"
            )

        end_date = None

        if student.group.is_graduated:
            end_date = spring_semester.end_date

        StudentGroupMembership.objects.create(
            student=student,
            group=student.group,
            start_date=date(student.group.year, 9, 1),
            end_date=end_date,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0007_academic_semester_schema'),
    ]

    operations = [
        migrations.RunPython(
            migrate_academic_data,
            migrations.RunPython.noop,
        ),
    ]