from django.db.models import Avg, Count
from django.shortcuts import render
from django.views.generic import TemplateView

from academics.models import Grade
from attendance.models import Attendance
from courses.models import Course
from students.models import Student
from teachers.models import Teacher


class DashboardView(TemplateView):
    """Public landing page for visitors, live dashboard for signed-in users."""

    template_name = 'dashboard/dashboard.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, 'core/landing.html', {})
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = getattr(getattr(self.request.user, 'profile', None), 'role', 'student')
        courses = Course.objects.select_related('teacher')
        attendance = Attendance.objects.select_related('student', 'course', 'course__teacher')
        grades = Grade.objects.select_related('student', 'course', 'course__teacher')
        students = Student.objects.all()

        if role == 'teacher':
            courses = courses.filter(teacher__email__iexact=self.request.user.email)
            attendance = attendance.filter(course__teacher__email__iexact=self.request.user.email)
            grades = grades.filter(course__teacher__email__iexact=self.request.user.email)
        elif role == 'student':
            students = students.filter(email__iexact=self.request.user.email)
            attendance = attendance.filter(student__email__iexact=self.request.user.email)
            grades = grades.filter(student__email__iexact=self.request.user.email)

        recent_students = list(students.order_by('-created_at').values('full_name', 'student_id', 'program', 'status')[:4])
        recent_grades = list(
            grades.order_by('-created_at').values('student__full_name', 'course__title', 'grade', 'marks')[:4]
        )
        context['role'] = role
        context['students_count'] = students.count() if role != 'teacher' else Student.objects.count()
        context['teachers_count'] = Teacher.objects.count() if role == 'administrator' else None
        context['courses_count'] = courses.count()
        context['attendance_count'] = attendance.count()
        present_count = attendance.filter(status='present').count()
        total_attendance = context['attendance_count']
        passing_count = grades.filter(marks__gte=60).count()
        total_grades = grades.count()
        context['attendance_percentage'] = round((present_count / total_attendance) * 100) if total_attendance else 0
        context['average_marks'] = round(grades.aggregate(value=Avg('marks'))['value'] or 0)
        context['passing_percentage'] = round((passing_count / total_grades) * 100) if total_grades else 0
        context['program_breakdown'] = students.values('program').annotate(total=Count('id')).order_by('program')[:4]
        context['react_dashboard_data'] = {
            'students_count': context['students_count'],
            'teachers_count': context['teachers_count'] or 0,
            'courses_count': context['courses_count'],
            'attendance_count': context['attendance_count'],
            'recent_students': recent_students,
            'recent_grades': recent_grades,
        }
        return context
