from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from .forms import TeacherForm
from .models import Teacher


class TeacherListView(RoleRequiredMixin, ListView):
    allowed_roles = ('administrator',)
    model = Teacher
    template_name = 'teachers/teacher_list.html'
    context_object_name = 'teachers'
    ordering = ['full_name']


class TeacherDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = ('administrator',)
    model = Teacher
    template_name = 'teachers/teacher_detail.html'


class TeacherCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ('administrator',)
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/teacher_form.html'


class TeacherUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ('administrator',)
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/teacher_form.html'


class TeacherDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ('administrator',)
    model = Teacher
    template_name = 'teachers/teacher_delete.html'
    success_url = reverse_lazy('teacher_list')
