from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegistrationForm
from .models import Profile


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # The user signal creates the default profile; registration sets
            # its explicitly selected, non-administrator role.
            Profile.objects.update_or_create(
                user=user,
                defaults={'role': form.cleaned_data['role']},
            )
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Account created successfully.')
            return redirect('dashboard')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={'role': 'administrator' if request.user.is_superuser else 'student'},
    )
    return render(request, 'accounts/profile.html', {'profile': profile})
