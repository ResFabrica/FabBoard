from django.urls import path
from . import views

app_name = 'fabmaintenance'

urlpatterns = [
    path('', views.machine_list, name='machine_list'),
    path('<int:pk>/', views.machine_detail, name='machine_detail'),
    path('<int:pk>/edit/', views.machine_edit, name='machine_edit'),
    path('add/', views.machine_add, name='machine_add'),
    path('<int:pk>/delete/', views.machine_delete, name='machine_delete'),
    path('maintenance/<int:pk>/complete/', views.complete_maintenance, name='complete_maintenance'),
    path('maintenance/<int:pk>/delete/', views.delete_maintenance, name='delete_maintenance'),
    path('maintenance/add/<int:machine_pk>/', views.add_maintenance, name='add_maintenance'),
    path('<int:pk>/public/', views.machine_public_view, name='machine_public_view'),
] 