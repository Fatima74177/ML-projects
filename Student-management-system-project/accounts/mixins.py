from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from courses.models import Course


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles = ()

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        profile = getattr(self.request.user, 'profile', None)
        return bool(profile and profile.role in self.allowed_roles)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, 'You do not have permission to access that page.')
            return redirect('dashboard')
        messages.error(self.request, 'You do not have permission to access that page.')
        return super().handle_no_permission()


class TeacherCourseScopedMixin:
    """Limit teachers to records and course choices they are assigned to."""

    def is_teacher(self):
        profile = getattr(self.request.user, 'profile', None)
        return bool(profile and profile.role == 'teacher' and not self.request.user.is_superuser)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.is_teacher():
            return queryset.filter(course__teacher__email__iexact=self.request.user.email)
        return queryset

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.is_teacher() and 'course' in form.fields:
            form.fields['course'].queryset = Course.objects.filter(
                teacher__email__iexact=self.request.user.email
            )
        return form
