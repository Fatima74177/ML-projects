from django.contrib.auth.models import User
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from academics.models import Grade
from attendance.models import Attendance
from courses.models import Course
from students.models import Student
from teachers.models import Teacher


@override_settings(
    MIDDLEWARE=[
        middleware
        for middleware in settings.MIDDLEWARE
        if middleware != 'whitenoise.middleware.WhiteNoiseMiddleware'
    ]
)
class RoleAccessTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin-password')
        self.teacher_user = User.objects.create_user('teacher', 'teacher@example.com', 'teacher-password')

        self.other_teacher = Teacher.objects.create(
            teacher_id='T-2', full_name='Other Teacher', email='other@example.com', department='Science'
        )
        self.teacher = Teacher.objects.create(
            teacher_id='T-1', full_name='Assigned Teacher', email='teacher@example.com', department='Science'
        )
        self.own_course = Course.objects.create(course_code='OWN-1', title='Own Course', teacher=self.teacher, schedule='Mon')
        self.other_course = Course.objects.create(
            course_code='OTHER-1', title='Other Course', teacher=self.other_teacher, schedule='Tue'
        )
        self.student = Student.objects.create(
            student_id='S-1', full_name='Student', email='student@example.com', program='Science', year='1'
        )
        self.own_attendance = Attendance.objects.create(student=self.student, course=self.own_course, attendance_date='2026-01-01')
        self.other_attendance = Attendance.objects.create(student=self.student, course=self.other_course, attendance_date='2026-01-02')
        self.own_grade = Grade.objects.create(student=self.student, course=self.own_course, exam_name='Quiz', marks=80, grade='A')
        self.other_grade = Grade.objects.create(student=self.student, course=self.other_course, exam_name='Quiz', marks=80, grade='A')

    def test_superuser_gets_administrator_profile_by_default(self):
        self.assertEqual(self.admin.profile.role, 'administrator')

    def test_teacher_account_is_corrected_from_its_teacher_record_on_login(self):
        self.client.force_login(self.teacher_user)
        self.teacher_user.profile.refresh_from_db()
        self.assertEqual(self.teacher_user.profile.role, 'teacher')

    def test_teacher_cannot_edit_or_delete_another_teachers_records(self):
        self.client.force_login(self.teacher_user)
        for name, record in (
            ('attendance_update', self.other_attendance),
            ('attendance_delete', self.other_attendance),
            ('academic_update', self.other_grade),
            ('academic_delete', self.other_grade),
        ):
            response = self.client.get(reverse(name, args=[record.pk]))
            self.assertEqual(response.status_code, 404)

    def test_teacher_form_offers_only_assigned_courses(self):
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('attendance_add'))
        courses = response.context['form'].fields['course'].queryset
        self.assertQuerySetEqual(courses, [self.own_course], ordered=False)

    def test_teacher_cannot_manage_student_profiles(self):
        self.client.force_login(self.teacher_user)
        self.assertEqual(self.client.get(reverse('student_add')).status_code, 302)
        self.assertEqual(self.client.get(reverse('student_update', args=[self.student.pk])).status_code, 302)

    def test_student_registration_creates_a_matching_student_record(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'new-student',
                'first_name': 'New',
                'last_name': 'Student',
                'email': 'new.student@example.com',
                'password1': 'Secure-pass-123',
                'password2': 'Secure-pass-123',
                'role': 'student',
            },
        )
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(Student.objects.filter(email='new.student@example.com').exists())
