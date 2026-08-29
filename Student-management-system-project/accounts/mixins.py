from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect


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
