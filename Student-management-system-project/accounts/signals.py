from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


def synchronize_profile_role(user):
    """Assign the portal role from the user's school record when available."""
    if user.is_superuser:
        role = 'administrator'
    else:
        # Import here so account creation does not create an app-loading cycle.
        from students.models import Student
        from teachers.models import Teacher

        if Teacher.objects.filter(email__iexact=user.email).exists():
            role = 'teacher'
        elif Student.objects.filter(email__iexact=user.email).exists():
            role = 'student'
        else:
            return Profile.objects.get_or_create(user=user, defaults={'role': 'student'})[0]

    profile, _ = Profile.objects.get_or_create(user=user, defaults={'role': role})
    if profile.role != role:
        profile.role = role
        profile.save(update_fields=['role'])
    return profile


@receiver(post_save, sender=User)
def create_or_promote_profile(sender, instance, **kwargs):
    """Keep every account linked to a profile with the correct default role."""
    default_role = 'administrator' if instance.is_superuser else 'student'
    profile, created = Profile.objects.get_or_create(
        user=instance,
        defaults={'role': default_role},
    )
    if instance.is_superuser and not created and profile.role != 'administrator':
        profile.role = 'administrator'
        profile.save(update_fields=['role'])


@receiver(user_logged_in)
def synchronize_role_on_login(sender, request, user, **kwargs):
    """Correct existing demo/staff accounts before their workspace is shown."""
    synchronize_profile_role(user)
