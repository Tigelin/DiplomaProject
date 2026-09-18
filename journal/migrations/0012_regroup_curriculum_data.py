from datetime import date

from django.db import migrations


CURRICULUM_NAME = 'Учебный план 2025/2026'


def regroup_curriculum_data(apps, schema_editor):
    AcademicSemester = apps.get_model('journal', 'AcademicSemester')
    SpecialtyCurriculum = apps.get_model('journal', 'SpecialtyCurriculum')
    SpecialtyCurriculumItem = apps.get_model('journal', 'SpecialtyCurriculumItem')
    AcademicSemesterCurriculum = apps.get_model('journal', 'AcademicSemesterCurriculum')

    curriculum_pairs = set(
        SpecialtyCurriculumItem.objects.values_list(
            'specialty_id',
            'study_semester',
        )
    )
    specialty_ids = {
        specialty_id
        for specialty_id, study_semester in curriculum_pairs
    }
    study_semesters = {
        study_semester
        for specialty_id, study_semester in curriculum_pairs
    }

    actual_counts = {
        'items': SpecialtyCurriculumItem.objects.count(),
        'pairs': len(curriculum_pairs),
        'specialties': len(specialty_ids),
    }
    expected_counts = {
        'items': 200,
        'pairs': 20,
        'specialties': 5,
    }

    if actual_counts != expected_counts or study_semesters != {2, 4, 6, 8}:
        raise RuntimeError(
            f"Unexpected curriculum data: {actual_counts}, "
            f"semesters: {sorted(study_semesters)}"
        )

    if SpecialtyCurriculum.objects.exists():
        raise RuntimeError(
            'Specialty curricula already exist'
        )

    if AcademicSemesterCurriculum.objects.exists():
        raise RuntimeError(
            'Academic semester curriculum selections already exist'
        )

    if SpecialtyCurriculumItem.objects.filter(curriculum__isnull=False).exists():
        raise RuntimeError(
            'Curriculum items are already linked to versions'
        )

    spring_semesters = AcademicSemester.objects.filter(
        start_year=2025,
        is_first_semester=False,
        start_date=date(2026, 1, 12),
        end_date=date(2026, 6, 27),
        status__code='CLOSED',
    )

    if spring_semesters.count() != 1:
        raise RuntimeError(
            'Closed spring 2025/2026 semester was not found'
        )

    spring_semester = spring_semesters.first()

    for specialty_id, study_semester in sorted(curriculum_pairs):
        curriculum = SpecialtyCurriculum.objects.create(
            name=CURRICULUM_NAME,
            specialty_id=specialty_id,
            study_semester=study_semester,
            is_approved=True,
            is_archived=False,
        )

        curriculum_items = SpecialtyCurriculumItem.objects.filter(
            specialty_id=specialty_id,
            study_semester=study_semester,
        )
        item_count = curriculum_items.count()
        updated_items = curriculum_items.update(
            curriculum=curriculum
        )

        if updated_items != item_count:
            raise RuntimeError(
                f"Failed to link curriculum items for specialty "
                f"{specialty_id}, semester {study_semester}"
            )

        AcademicSemesterCurriculum.objects.create(
            semester=spring_semester,
            curriculum=curriculum,
        )

    result_counts = {
        'curriculums': SpecialtyCurriculum.objects.count(),
        'selections': AcademicSemesterCurriculum.objects.count(),
        'linked_items': SpecialtyCurriculumItem.objects.filter(
            curriculum__isnull=False
        ).count(),
        'unlinked_items': SpecialtyCurriculumItem.objects.filter(
            curriculum__isnull=True
        ).count(),
    }
    expected_result_counts = {
        'curriculums': 20,
        'selections': 20,
        'linked_items': 200,
        'unlinked_items': 0,
    }

    if result_counts != expected_result_counts:
        raise RuntimeError(
            f"Unexpected versioned curriculum counts: {result_counts}"
        )


def reverse_curriculum_data(apps, schema_editor):
    SpecialtyCurriculum = apps.get_model('journal', 'SpecialtyCurriculum')
    SpecialtyCurriculumItem = apps.get_model('journal', 'SpecialtyCurriculumItem')
    AcademicSemesterCurriculum = apps.get_model('journal', 'AcademicSemesterCurriculum')

    curriculum_ids = list(
        AcademicSemesterCurriculum.objects.filter(
            semester__start_year=2025,
            semester__is_first_semester=False,
            curriculum__name=CURRICULUM_NAME,
        ).values_list(
            'curriculum_id',
            flat=True,
        )
    )

    SpecialtyCurriculumItem.objects.filter(
        curriculum_id__in=curriculum_ids
    ).update(
        curriculum=None
    )
    AcademicSemesterCurriculum.objects.filter(
        curriculum_id__in=curriculum_ids
    ).delete()
    SpecialtyCurriculum.objects.filter(
        id__in=curriculum_ids
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0011_versioned_curriculum_schema'),
    ]

    operations = [
        migrations.RunPython(
            regroup_curriculum_data,
            reverse_curriculum_data,
        ),
    ]