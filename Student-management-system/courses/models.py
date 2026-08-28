from django.db import models
from django.urls import reverse


class Course(models.Model):
    course_code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=150)
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    schedule = models.CharField(max_length=120)
    credits = models.PositiveSmallIntegerField(default=3)
    capacity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('course_detail', args=[self.pk])
