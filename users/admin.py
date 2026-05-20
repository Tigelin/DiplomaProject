from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'last_name', 'first_name', 'patronymic', 'email', 'role', 'is_staff')
    list_filter = ('role', 'is_staff')
    search_fields = ('username', 'last_name', 'first_name', 'patronymic')

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('role', 'phone', 'patronymic')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительно', {'fields': ('role', 'phone', 'patronymic')}),
    )