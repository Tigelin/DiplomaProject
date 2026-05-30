from django.db import models

# Create your models here.
from django.db import models
from users.models import User


class Department(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название отделения")
    address = models.CharField(max_length=200, verbose_name="Адрес", blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Отделение"
        verbose_name_plural = "Отделения"


class Group(models.Model):
    name = models.CharField(max_length=50, verbose_name="Номер группы")
    year = models.IntegerField(verbose_name="Год поступления")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="Отделение")

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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "План дисциплины"
        verbose_name_plural = "Планы дисциплин"


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


class Discipline(models.Model):
    plan = models.ForeignKey(DisciplinePlan, on_delete=models.CASCADE, verbose_name="План дисциплины")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name="Группа")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name="Преподаватель")

    def __str__(self):
        return f"{self.plan.name} - {self.group.name}"

    class Meta:
        verbose_name = "Дисциплина"
        verbose_name_plural = "Дисциплины"
        unique_together = ['plan', 'group', 'teacher']


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
    name = models.CharField(max_length=200, verbose_name="Название задания")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='tasks', verbose_name="Занятие")
    description = models.TextField(blank=True, verbose_name="Описание задания")

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