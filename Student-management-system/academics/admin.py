from django.contrib import admin

from .models import Grade


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'exam_name', 'marks', 'grade')
    search_fields = ('student__full_name', 'course__title', 'exam_name')

# Register your models here.
