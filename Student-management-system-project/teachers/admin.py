from django.contrib import admin

from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher_id', 'full_name', 'email', 'department', 'status')
    search_fields = ('teacher_id', 'full_name', 'email', 'department')

# Register your models here.
