from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from students.models import Student


class Command(BaseCommand):
    help = 'Create Student records for existing accounts whose profile role is student.'

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        users = User.objects.filter(profile__role='student').order_by('pk')

        for user in users:
            if not user.email:
                skipped += 1
                self.stdout.write(self.style.WARNING(f'Skipped {user.username}: no email address.'))
                continue

            student, was_created = Student.objects.get_or_create(
                email=user.email,
                defaults={
                    'student_id': f'ST-{user.pk:05d}',
                    'full_name': user.get_full_name() or user.username,
                    'program': 'Not assigned',
                    'year': 'Not assigned',
                    'status': 'active',
                },
            )
            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Student account sync complete: {created} created, {skipped} skipped.'
            )
        )
