from django.db import models
from django.urls import reverse


class Grade(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='grades')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='grades')
    exam_name = models.CharField(max_length=120)
    marks = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=3)
    remarks = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student} - {self.course} - {self.grade}'

    def get_absolute_url(self):
        return reverse('academic_detail', args=[self.pk])
