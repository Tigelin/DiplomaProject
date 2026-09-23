from django.db import models

# Create your models here.
from django.db import models
from users.models import User
from django.core.exceptions import ValidationError


class Department(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название отделения")
    address = models.CharField(max_length=200, verbose_name="Адрес", blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Отделение"
        verbose_name_plural = "Отделения"


class Specialty(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название специальности")
    code = models.CharField(max_length=20, verbose_name="Код специальности", blank=True)
    qualification = models.CharField(max_length=200, verbose_name="Квалификация", blank=True)
    description = models.TextField(verbose_name="Описание", blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="Отделение")
    duration_semesters = models.PositiveSmallIntegerField(default=8, verbose_name="Продолжительность обучения в семестрах")

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name

    class Meta:
        verbose_name = "Специальность"
        verbose_name_plural = "Специальности"


class GroupNumberSet(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название комплекта")
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, verbose_name="Специальность")

    def __str__(self):
        return f"{self.name} ({self.specialty})"

    class Meta:
        verbose_name = "Комплект номеров групп"
        verbose_name_plural = "Комплекты номеров групп"
        unique_together = ['name', 'specialty']


class GroupNumberEntry(models.Model):
    number_set = models.ForeignKey(GroupNumberSet, on_delete=models.CASCADE, related_name='entries', verbose_name="Комплект")
    course = models.PositiveSmallIntegerField(verbose_name="Курс")
    name = models.CharField(max_length=50, verbose_name="Номер группы")

    def __str__(self):
        return f"{self.course} курс — {self.name}"

    class Meta:
        verbose_name = "Номер группы по курсу"
        verbose_name_plural = "Номера групп по курсам"
        unique_together = ['number_set', 'course']


class Group(models.Model):
    name = models.CharField(max_length=50, verbose_name="Номер группы")
    year = models.IntegerField(verbose_name="Год поступления")
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, verbose_name="Специальность")
    is_graduated = models.BooleanField(default=False, verbose_name="Обучение завершено")
    number_set = models.ForeignKey(GroupNumberSet, on_delete=models.PROTECT, verbose_name="Комплект номеров")

    def get_study_semester(self, semester):
        return (semester.start_year - self.year) * 2 + semester.number

    def get_course(self, semester):
        return (self.get_study_semester(semester) + 1) // 2

    def get_display_name(self, semester):
        if not self.number_set:
            return self.name

        entry = self.number_set.entries.filter(course=self.get_course(semester)).first()
        return entry.name if entry else self.name

    def __str__(self):
        return f"{self.name} ({self.year})"

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"


class LessonType(models.Model):
    name = models.CharField(max_length=50, verbose_name="Тип занятия")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип занятия"
        verbose_name_plural = "Типы занятий"


class TaskType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название типа")
    abbreviation = models.CharField(max_length=10, unique=True, verbose_name="Аббревиатура")

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

    class Meta:
        verbose_name = "Тип задания"
        verbose_name_plural = "Типы заданий"


class AttendanceType(models.Model):
    name = models.CharField(max_length=50, verbose_name="Тип присутствия")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип присутствия"
        verbose_name_plural = "Типы присутствия"


class MessageStatus(models.Model):
    name = models.CharField(max_length=50, verbose_name="Статус")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Статус сообщения"
        verbose_name_plural = "Статусы сообщений"


class Classroom(models.Model):
    number = models.CharField(max_length=20, verbose_name="Номер кабинета")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="Отделение")

    def __str__(self):
        return f"Каб. {self.number} ({self.department.name})"

    class Meta:
        verbose_name = "Кабинет"
        verbose_name_plural = "Кабинеты"


class DisciplinePlan(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название дисциплины")
    total_hours = models.IntegerField(verbose_name="Общее количество часов")
    is_approved = models.BooleanField(default=False, verbose_name="Утверждён")
    is_archived = models.BooleanField(default=False, verbose_name="В архиве")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "План дисциплины"
        verbose_name_plural = "Планы дисциплин"


class SpecialtyCurriculum(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, verbose_name="Специальность")
    study_semester = models.PositiveSmallIntegerField(verbose_name="Семестр обучения")
    is_approved = models.BooleanField(default=False, verbose_name="Утверждён")
    is_archived = models.BooleanField(default=False, verbose_name="В архиве")

    def clean(self):
        super().clean()

        if self.specialty_id and self.study_semester:
            if self.study_semester < 1 or self.study_semester > self.specialty.duration_semesters:
                raise ValidationError({
                    'study_semester': 'Выбран неверный семестр обучения.'
                })

    def __str__(self):
        return f"{self.name} — {self.specialty}, {self.study_semester} семестр"

    class Meta:
        verbose_name = "Учебный план специальности"
        verbose_name_plural = "Учебные планы специальностей"
        unique_together = ['name', 'specialty', 'study_semester']


class SpecialtyCurriculumItem(models.Model):
    curriculum = models.ForeignKey(SpecialtyCurriculum, on_delete=models.CASCADE, related_name='items', verbose_name="Учебный план")
    plan = models.ForeignKey(DisciplinePlan, on_delete=models.PROTECT, limit_choices_to={'is_approved': True}, verbose_name="План дисциплины")

    def __str__(self):
        return f"{self.curriculum} — {self.plan}"

    class Meta:
        verbose_name = "Дисциплина учебного плана специальности"
        verbose_name_plural = "Дисциплины учебных планов специальностей"
        unique_together = ['curriculum', 'plan']


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    class Meta:
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    special_number = models.CharField(max_length=20, unique=True, verbose_name="Специальный номер")
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, verbose_name="Группа")

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.special_number})"

    class Meta:
        verbose_name = "Студент"
        verbose_name_plural = "Студенты"


class StudentGroupMembership(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='group_memberships', verbose_name="Студент")
    group = models.ForeignKey(Group, on_delete=models.PROTECT, verbose_name="Группа")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(null=True, blank=True, verbose_name="Дата окончания")

    def clean(self):
        super().clean()

        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({
                'end_date': 'Дата окончания должна быть не раньше даты начала.'
            })

        if self.student_id and self.start_date:
            memberships = StudentGroupMembership.objects.filter(student_id=self.student_id).exclude(pk=self.pk)

            if self.end_date:
                memberships = memberships.filter(start_date__lte=self.end_date)

            memberships = memberships.filter(
                models.Q(end_date__isnull=True) |
                models.Q(end_date__gte=self.start_date)
            )

            if memberships.exists():
                raise ValidationError(
                    'Период обучения пересекается с другой группой студента.'
                )

    def __str__(self):
        return f"{self.student} — {self.group}"

    class Meta:
        verbose_name = "История группы студента"
        verbose_name_plural = "История групп студентов"
        unique_together = ['student', 'start_date']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__isnull=True) | models.Q(end_date__gte=models.F('start_date')),
                name='student_membership_dates_order',
            ),
        ]


class AcademicSemesterStatus(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name="Код")
    name = models.CharField(max_length=50, unique=True, verbose_name="Название")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Статус учебного семестра"
        verbose_name_plural = "Статусы учебных семестров"


class AcademicSemester(models.Model):
    start_year = models.PositiveIntegerField(verbose_name="Год начала учебного года")
    is_first_semester = models.BooleanField(default=True, verbose_name="Первый семестр")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    status = models.ForeignKey(AcademicSemesterStatus, on_delete=models.PROTECT, verbose_name="Статус")

    @property
    def number(self):
        return 1 if self.is_first_semester else 2

    def clean(self):
        super().clean()

        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError({
                    'end_date': 'Дата окончания должна быть не раньше даты начала.'
                })

            overlapping_semesters = AcademicSemester.objects.exclude(pk=self.pk).filter(
                start_date__lte=self.end_date,
                end_date__gte=self.start_date,
            )
            if overlapping_semesters.exists():
                raise ValidationError(
                    'Период пересекается с другим учебным семестром.'
                )

    def __str__(self):
        return f"{self.start_year}/{self.start_year + 1}, {self.number} семестр"

    class Meta:
        verbose_name = "Учебный семестр"
        verbose_name_plural = "Учебные семестры"
        unique_together = ['start_year', 'is_first_semester']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(start_date__lte=models.F('end_date')),
                name='academic_semester_dates_order',
            ),
        ]


class AcademicSemesterCurriculum(models.Model):
    semester = models.ForeignKey(AcademicSemester, on_delete=models.CASCADE, related_name='curriculum_selections', verbose_name="Учебный семестр")
    curriculum = models.ForeignKey(SpecialtyCurriculum, on_delete=models.PROTECT, related_name='semester_selections', verbose_name="Учебный план")

    def clean(self):
        super().clean()

        if self.curriculum_id:
            if not self.curriculum.is_approved or self.curriculum.is_archived:
                raise ValidationError({
                    'curriculum': 'Выберите утверждённый учебный план, который не находится в архиве.'
                })

        if self.semester_id and self.curriculum_id:
            selected_curriculums = AcademicSemesterCurriculum.objects.filter(
                semester_id=self.semester_id,
                curriculum__specialty_id=self.curriculum.specialty_id,
                curriculum__study_semester=self.curriculum.study_semester
            ).exclude(pk=self.pk)

            if selected_curriculums.exists():
                raise ValidationError(
                    'Для этой специальности и семестра обучения учебный план уже выбран.'
                )

    def __str__(self):
        return f"{self.semester} — {self.curriculum}"

    class Meta:
        verbose_name = "Учебный план учебного семестра"
        verbose_name_plural = "Учебные планы учебных семестров"
        unique_together = ['semester', 'curriculum']


class Discipline(models.Model):
    plan = models.ForeignKey(DisciplinePlan, on_delete=models.CASCADE, verbose_name="План дисциплины")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name="Группа")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Преподаватель")
    semester = models.ForeignKey(AcademicSemester, on_delete=models.PROTECT, verbose_name="Учебный семестр")
    is_confirmed = models.BooleanField(default=False, verbose_name="Подтверждена")

    def get_group_display_name(self):
        return self.group.get_display_name(self.semester)

    def __str__(self):
        return f"{self.plan.name} - {self.group.name}"

    class Meta:
        verbose_name = "Дисциплина"
        verbose_name_plural = "Дисциплины"
        unique_together = ['plan', 'group', 'semester']


class Schedule(models.Model):
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, verbose_name="Дисциплина")
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, verbose_name="Кабинет")
    lesson_number = models.IntegerField(verbose_name="Номер пары")
    date = models.DateField(verbose_name="Дата занятия")

    def __str__(self):
        return f"{self.date} - {self.lesson_number} пара: {self.discipline}"

    class Meta:
        verbose_name = "Расписание"
        verbose_name_plural = "Расписания"
        unique_together = ['discipline', 'date', 'lesson_number']


class Lesson(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, verbose_name="Расписание")
    topic = models.CharField(max_length=200, verbose_name="Тема занятия", blank=True)
    lesson_type = models.ForeignKey(LessonType, on_delete=models.SET_NULL, null=True, verbose_name="Тип занятия")
    hours = models.IntegerField(default=2, verbose_name="Количество часов")

    def __str__(self):
        return f"{self.schedule} - {self.topic or 'Без темы'}"

    class Meta:
        verbose_name = "Занятие"
        verbose_name_plural = "Занятия"


class Task(models.Model):
    task_type = models.ForeignKey(TaskType, on_delete=models.PROTECT, verbose_name="Тип задания")
    name = models.CharField(max_length=200, verbose_name="Название задания")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='tasks', verbose_name="Занятие")
    description = models.TextField(blank=True, verbose_name="Описание задания")
    required_students = models.ManyToManyField(Student, blank=True, related_name='required_tasks', verbose_name="Обязательно для студентов")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Задание"
        verbose_name_plural = "Задания"


class LessonFile(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название файла")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='files', verbose_name="Занятие")
    file = models.FileField(upload_to='lesson_files/', verbose_name="Файл")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Время загрузки")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Файл занятия"
        verbose_name_plural = "Файлы занятий"


class Grade(models.Model):
    value = models.IntegerField(verbose_name="Оценка")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='grades', verbose_name="Задание")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Студент")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время выставления")

    def __str__(self):
        return f"{self.student} - {self.task} - {self.value}"

    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"
        unique_together = ['task', 'student']


class Attendance(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attendances', verbose_name="Занятие")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Студент")
    attendance_type = models.ForeignKey(AttendanceType, on_delete=models.SET_NULL, null=True,
                                        verbose_name="Тип присутствия")

    def __str__(self):
        return f"{self.student} - {self.lesson} - {self.attendance_type}"

    class Meta:
        verbose_name = "Присутствие"
        verbose_name_plural = "Присутствия"
        unique_together = ['lesson', 'student']


class ContactMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name="Имя")
    email = models.EmailField(verbose_name="Email")
    message = models.TextField(verbose_name="Сообщение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    status = models.ForeignKey(MessageStatus, on_delete=models.SET_NULL, null=True, default=None,
                               verbose_name="Статус сообщения")

    def __str__(self):
        return f"{self.name} - {self.created_at}"

    class Meta:
        verbose_name = "Контактное сообщение"
        verbose_name_plural = "Контактные сообщения"
