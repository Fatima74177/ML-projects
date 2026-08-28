from django.urls import path

from .views import GradeCreateView, GradeDeleteView, GradeDetailView, GradeListView, GradeUpdateView

urlpatterns = [
    path('', GradeListView.as_view(), name='academic_list'),
    path('add/', GradeCreateView.as_view(), name='academic_add'),
    path('<int:pk>/', GradeDetailView.as_view(), name='academic_detail'),
    path('<int:pk>/edit/', GradeUpdateView.as_view(), name='academic_update'),
    path('<int:pk>/delete/', GradeDeleteView.as_view(), name='academic_delete'),
]
