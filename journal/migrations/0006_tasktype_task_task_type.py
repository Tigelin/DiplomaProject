import random

import django.db.models.deletion
from django.db import migrations, models


TASK_TYPES = [
    ('Ответ на занятии', 'ОЗ'),
    ('Практическая работа', 'ПР'),
    ('Лабораторная работа', 'ЛР'),
    ('Самостоятельная работа', 'СР'),
    ('Контрольная работа', 'КР'),
    ('Тест', 'Т'),
    ('Проект', 'П'),
]


def create_task_types_and_assign_tasks(apps, schema_editor):
    TaskType = apps.get_model('journal', 'TaskType')
    Task = apps.get_model('journal', 'Task')

    task_types = [
        TaskType.objects.create(
            name=name,
            abbreviation=abbreviation
        )
        for name, abbreviation in TASK_TYPES
    ]

    tasks = list(Task.objects.order_by('id'))
    randomizer = random.Random(20260915)

    for index, task in enumerate(tasks):
        if index < len(task_types):
            task_type = task_types[index]
        else:
            task_type = randomizer.choice(task_types)

        task.task_type_id = task_type.id

    Task.objects.bulk_update(tasks, ['task_type'])


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0005_task_required_students'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskType',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'name',
                    models.CharField(
                        max_length=100,
                        unique=True,
                        verbose_name='Название типа'
                    )
                ),
                (
                    'abbreviation',
                    models.CharField(
                        max_length=10,
                        unique=True,
                        verbose_name='Аббревиатура'
                    )
                ),
            ],
            options={
                'verbose_name': 'Тип задания',
                'verbose_name_plural': 'Типы заданий',
            },
        ),
        migrations.AddField(
            model_name='task',
            name='task_type',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='journal.tasktype',
                verbose_name='Тип задания'
            ),
        ),
        migrations.RunPython(
            create_task_types_and_assign_tasks,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='task',
            name='task_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='journal.tasktype',
                verbose_name='Тип задания'
            ),
        ),
    ]