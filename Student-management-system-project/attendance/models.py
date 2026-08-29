from django.db import models
from django.urls import reverse


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='attendance_records')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='attendance_records')
    attendance_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student} - {self.course} - {self.attendance_date}'

    def get_absolute_url(self):
        return reverse('attendance_detail', args=[self.pk])
