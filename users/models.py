from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"


class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    patronymic = models.CharField(max_length=100, blank=True, verbose_name="Отчество")

    def __str__(self):
        return self.username

    def get_full_name(self):
        parts = [self.last_name, self.first_name, self.patronymic]
        return ' '.join([p for p in parts if p])

    def get_short_name(self):
        initials = ''
        if self.first_name:
            initials += self.first_name[0] + '.'
        if self.patronymic:
            initials += self.patronymic[0] + '.'
        return f"{self.last_name} {initials}".strip()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"