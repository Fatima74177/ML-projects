from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from academics.models import Grade
from accounts.models import Profile
from attendance.models import Attendance
from courses.models import Course
from students.models import Student
from teachers.models import Teacher


class Command(BaseCommand):
    help = 'Create demo users and sample academic records.'

    def handle(self, *args, **options):
        self.create_user('admin', 'admin@example.com', 'admin12345', 'administrator', True, True)
        self.create_user('teacher', 'teacher@example.com', 'teacher12345', 'teacher')
        self.create_user('student', 'student@example.com', 'student12345', 'student')

        students = [
            ('ST-1001', 'Ayesha Khan', 'student@example.com', 'Computer Science', 'Year 3'),
            ('ST-1002', 'Hamza Ali', 'hamza.ali@example.com', 'Business Administration', 'Year 2'),
            ('ST-1003', 'Sara Ahmed', 'sara.ahmed@example.com', 'Software Engineering', 'Year 1'),
            ('ST-1004', 'Zain Raza', 'zain.raza@example.com', 'Computer Science', 'Year 2'),
        ]
        for student_id, full_name, email, program, year in students:
            Student.objects.update_or_create(
                student_id=student_id,
                defaults={
                    'full_name': full_name,
                    'email': email,
                    'program': program,
                    'year': year,
                    'phone': '0300-0000000',
                    'address': 'Campus hostel',
                    'status': 'active',
                },
            )

        teachers = [
            ('TC-201', 'Dr. Farah Malik', 'teacher@example.com', 'Computer Science'),
            ('TC-202', 'Omar Siddiqui', 'omar.siddiqui@example.com', 'Business'),
            ('TC-203', 'Hina Shah', 'hina.shah@example.com', 'Mathematics'),
        ]
        for teacher_id, full_name, email, department in teachers:
            Teacher.objects.update_or_create(
                teacher_id=teacher_id,
                defaults={
                    'full_name': full_name,
                    'email': email,
                    'department': department,
                    'phone': '0311-0000000',
                    'status': 'active',
                },
            )

        farah = Teacher.objects.get(teacher_id='TC-201')
        omar = Teacher.objects.get(teacher_id='TC-202')
        hina = Teacher.objects.get(teacher_id='TC-203')
        courses = [
            ('CS-301', 'Data Structures', farah, 'Mon & Wed - 10:00 AM', 3, 40),
            ('CS-310', 'Web Engineering', farah, 'Tue & Thu - 11:30 AM', 3, 35),
            ('BA-202', 'Marketing Principles', omar, 'Mon & Wed - 1:00 PM', 3, 45),
            ('MA-115', 'Discrete Mathematics', hina, 'Fri - 9:00 AM', 3, 40),
        ]
        for code, title, teacher, schedule, credits, capacity in courses:
            Course.objects.update_or_create(
                course_code=code,
                defaults={
                    'title': title,
                    'teacher': teacher,
                    'schedule': schedule,
                    'credits': credits,
                    'capacity': capacity,
                    'description': f'{title} course for the current academic term.',
                },
            )

        today = date.today()
        statuses = ['present', 'present', 'late', 'absent']
        for index, student in enumerate(Student.objects.order_by('student_id')):
            for course in Course.objects.order_by('course_code')[:2]:
                Attendance.objects.update_or_create(
                    student=student,
                    course=course,
                    attendance_date=today - timedelta(days=index),
                    defaults={'status': statuses[index % len(statuses)]},
                )

        grade_rows = [
            ('ST-1001', 'CS-301', 'Midterm', 91, 'A+'),
            ('ST-1002', 'BA-202', 'Midterm', 78, 'B+'),
            ('ST-1003', 'CS-310', 'Quiz 1', 95, 'A+'),
            ('ST-1004', 'CS-301', 'Assignment', 72, 'B'),
        ]
        for student_id, course_code, exam_name, marks, grade in grade_rows:
            Grade.objects.update_or_create(
                student=Student.objects.get(student_id=student_id),
                course=Course.objects.get(course_code=course_code),
                exam_name=exam_name,
                defaults={'marks': marks, 'grade': grade, 'remarks': 'Demo academic record'},
            )

        self.stdout.write(self.style.SUCCESS('Demo data created successfully.'))

    def create_user(self, username, email, password, role, is_staff=False, is_superuser=False):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': is_staff,
                'is_superuser': is_superuser,
            },
        )
        if created:
            user.set_password(password)
            user.save()
        Profile.objects.update_or_create(user=user, defaults={'role': role})
