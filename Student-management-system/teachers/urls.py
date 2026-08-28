from django.urls import path

from .views import TeacherCreateView, TeacherDeleteView, TeacherDetailView, TeacherListView, TeacherUpdateView

urlpatterns = [
    path('', TeacherListView.as_view(), name='teacher_list'),
    path('add/', TeacherCreateView.as_view(), name='teacher_add'),
    path('<int:pk>/', TeacherDetailView.as_view(), name='teacher_detail'),
    path('<int:pk>/edit/', TeacherUpdateView.as_view(), name='teacher_update'),
    path('<int:pk>/delete/', TeacherDeleteView.as_view(), name='teacher_delete'),
]
