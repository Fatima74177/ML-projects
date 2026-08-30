from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin, TeacherCourseScopedMixin
from .forms import GradeForm
from .models import Grade


class GradeListView(LoginRequiredMixin, ListView):
    model = Grade
    template_name = 'academics/academic_list.html'
    context_object_name = 'grades'
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset().select_related('student', 'course', 'course__teacher')
        profile = getattr(self.request.user, 'profile', None)
        if profile and profile.role == 'teacher':
            return queryset.filter(course__teacher__email__iexact=self.request.user.email)
        if profile and profile.role == 'student':
            return queryset.filter(student__email__iexact=self.request.user.email)
        return queryset


class GradeDetailView(LoginRequiredMixin, DetailView):
    model = Grade
    template_name = 'academics/academic_detail.html'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('student', 'course', 'course__teacher')
        profile = getattr(self.request.user, 'profile', None)
        if profile and profile.role == 'teacher':
            return queryset.filter(course__teacher__email__iexact=self.request.user.email)
        if profile and profile.role == 'student':
            return queryset.filter(student__email__iexact=self.request.user.email)
        return queryset


class GradeCreateView(RoleRequiredMixin, TeacherCourseScopedMixin, CreateView):
    allowed_roles = ('administrator', 'teacher')
    model = Grade
    form_class = GradeForm
    template_name = 'academics/academic_form.html'


class GradeUpdateView(RoleRequiredMixin, TeacherCourseScopedMixin, UpdateView):
    allowed_roles = ('administrator', 'teacher')
    model = Grade
    form_class = GradeForm
    template_name = 'academics/academic_form.html'


class GradeDeleteView(RoleRequiredMixin, TeacherCourseScopedMixin, DeleteView):
    allowed_roles = ('administrator', 'teacher')
    model = Grade
    template_name = 'academics/academic_delete.html'
    success_url = reverse_lazy('academic_list')
