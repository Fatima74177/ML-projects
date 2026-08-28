from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from .forms import CourseForm
from .models import Course


class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    ordering = ['course_code']

    def get_queryset(self):
        queryset = super().get_queryset().select_related('teacher')
        profile = getattr(self.request.user, 'profile', None)
        if profile and profile.role == 'teacher':
            return queryset.filter(teacher__email__iexact=self.request.user.email)
        return queryset


class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'courses/course_detail.html'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('teacher')
        profile = getattr(self.request.user, 'profile', None)
        if profile and profile.role == 'teacher':
            return queryset.filter(teacher__email__iexact=self.request.user.email)
        return queryset


class CourseCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ('administrator',)
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'


class CourseUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ('administrator',)
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'


class CourseDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ('administrator',)
    model = Course
    template_name = 'courses/course_delete.html'
    success_url = reverse_lazy('course_list')
