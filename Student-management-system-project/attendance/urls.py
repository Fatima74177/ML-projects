from django.urls import path

from .views import AttendanceCreateView, AttendanceDeleteView, AttendanceDetailView, AttendanceListView, AttendanceUpdateView

urlpatterns = [
    path('', AttendanceListView.as_view(), name='attendance_list'),
    path('add/', AttendanceCreateView.as_view(), name='attendance_add'),
    path('<int:pk>/', AttendanceDetailView.as_view(), name='attendance_detail'),
    path('<int:pk>/edit/', AttendanceUpdateView.as_view(), name='attendance_update'),
    path('<int:pk>/delete/', AttendanceDeleteView.as_view(), name='attendance_delete'),
]
