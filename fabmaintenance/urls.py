from django.urls import path
from . import views

app_name = 'fabmaintenance'

urlpatterns = [
    path('machines/', views.machine_list, name='machine_list'),
    path('machines/<int:pk>/', views.machine_detail, name='machine_detail'),
    path('machines/<int:pk>/edit/', views.machine_edit, name='machine_edit'),
    path('machines/<int:pk>/delete/', views.machine_delete, name='machine_delete'),
    path('maintenance/<int:pk>/complete/', views.complete_maintenance, name='complete_maintenance'),
    path('maintenance/<int:pk>/delete/', views.delete_maintenance, name='delete_maintenance'),
    path('maintenance/add/<int:machine_pk>/', views.add_maintenance, name='add_maintenance'),
    path('machines/<int:pk>/public/', views.machine_public_view, name='machine_public_view'),
    path('machines/<int:machine_pk>/maintenance/', views.maintenance_ajax, name='maintenance_ajax'),
    path('maintenance/names/', views.get_maintenance_names, name='get_maintenance_names'),
    
    # URLs du catalogue
    path('catalogue/', views.machine_catalogue, name='machine_catalogue'),
    path('catalogue/<int:pk>/', views.machine_template_detail, name='machine_template_detail'),
    path('catalogue/<int:pk>/create-machine/', views.create_machine_from_template, name='create_machine_from_template'),
    path('catalogue/create/', views.machine_template_create, name='machine_template_create'),
    path('catalogue/<int:pk>/edit/', views.machine_template_edit, name='machine_template_edit'),
    path('catalogue/<int:pk>/delete/', views.machine_template_delete, name='machine_template_delete'),
    path('catalogue/<int:pk>/duplicate/', views.machine_template_duplicate, name='machine_template_duplicate'),
    path('catalogue/<int:pk>/maintenances/', views.template_maintenance_list, name='template_maintenance_list'),
    path('catalogue/<int:pk>/maintenances/add/', views.template_maintenance_add, name='template_maintenance_add'),
    path('catalogue/<int:template_pk>/maintenances/<int:pk>/edit/', views.template_maintenance_edit, name='template_maintenance_edit'),
    path('catalogue/<int:template_pk>/maintenances/<int:pk>/delete/', views.template_maintenance_delete, name='template_maintenance_delete'),
    path('catalogue/<int:template_pk>/maintenance/', views.template_maintenance_ajax, name='template_maintenance_ajax'),
] 