from django.urls import path

from .views import CourseCreateView, CourseDeleteView, CourseDetailView, CourseListView, CourseUpdateView

urlpatterns = [
    path('', CourseListView.as_view(), name='course_list'),
    path('add/', CourseCreateView.as_view(), name='course_add'),
    path('<int:pk>/', CourseDetailView.as_view(), name='course_detail'),
    path('<int:pk>/edit/', CourseUpdateView.as_view(), name='course_update'),
    path('<int:pk>/delete/', CourseDeleteView.as_view(), name='course_delete'),
]
