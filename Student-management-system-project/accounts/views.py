from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegistrationForm
from .models import Profile
from .signals import synchronize_profile_role
from students.models import Student


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
            if form.cleaned_data['role'] == 'student':
                Student.objects.get_or_create(
                    email=user.email,
                    defaults={
                        'student_id': f'ST-{user.pk:05d}',
                        'full_name': user.get_full_name() or user.username,
                        'program': 'Not assigned',
                        'year': 'Not assigned',
                        'status': 'active',
                    },
                )
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Account created successfully.')
            return redirect('dashboard')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    profile = synchronize_profile_role(request.user)
    return render(request, 'accounts/profile.html', {'profile': profile})
