from django.contrib import admin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'attendance_date', 'status')
    search_fields = ('student__full_name', 'course__title')

# Register your models here.
