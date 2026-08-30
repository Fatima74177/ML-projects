from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from .forms import StudentForm
from .models import Student


class StudentListView(RoleRequiredMixin, ListView):
    allowed_roles = ('administrator', 'teacher')
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    ordering = ['full_name']


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        profile = getattr(self.request.user, 'profile', None)
        if profile and profile.role == 'student':
            return queryset.filter(email__iexact=self.request.user.email)
        return queryset


class StudentCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ('administrator',)
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'


class StudentUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ('administrator',)
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'


class StudentDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ('administrator',)
    model = Student
    template_name = 'students/student_delete.html'
    success_url = reverse_lazy('student_list')
