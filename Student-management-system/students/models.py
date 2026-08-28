from django.db import models
from django.urls import reverse


class Student(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('graduated', 'Graduated'),
    ]

    student_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    program = models.CharField(max_length=120)
    year = models.CharField(max_length=20)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse('student_detail', args=[self.pk])
