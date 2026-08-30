from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


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
