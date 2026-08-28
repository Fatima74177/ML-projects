from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from .forms import AttendanceForm
from .models import Attendance


class AttendanceListView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = 'attendance/attendance_list.html'
    context_object_name = 'attendance_records'
    ordering = ['-attendance_date']

    def get_queryset(self):
        queryset = super().get_queryset().select_related('student', 'course', 'course__teacher')
        profile = getattr(self.request.user, 'profile', None)
        if profile and profile.role == 'teacher':
            return queryset.filter(course__teacher__email__iexact=self.request.user.email)
        if profile and profile.role == 'student':
            return queryset.filter(student__email__iexact=self.request.user.email)
        return queryset


class AttendanceDetailView(LoginRequiredMixin, DetailView):
    model = Attendance
    template_name = 'attendance/attendance_detail.html'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('student', 'course', 'course__teacher')
        profile = getattr(self.request.user, 'profile', None)
        if profile and profile.role == 'teacher':
            return queryset.filter(course__teacher__email__iexact=self.request.user.email)
        if profile and profile.role == 'student':
            return queryset.filter(student__email__iexact=self.request.user.email)
        return queryset


class AttendanceCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ('administrator', 'teacher')
    model = Attendance
    form_class = AttendanceForm
    template_name = 'attendance/attendance_form.html'


class AttendanceUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ('administrator', 'teacher')
    model = Attendance
    form_class = AttendanceForm
    template_name = 'attendance/attendance_form.html'


class AttendanceDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ('administrator', 'teacher')
    model = Attendance
    template_name = 'attendance/attendance_delete.html'
    success_url = reverse_lazy('attendance_list')
