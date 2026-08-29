from django.contrib import admin

from .models import Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'title', 'teacher', 'schedule', 'credits', 'capacity')
    search_fields = ('course_code', 'title', 'schedule')

# Register your models here.
