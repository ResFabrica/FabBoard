from django.urls import path
from . import views

app_name = 'fabjobs'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Jobs
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/update/', views.job_update, name='job_update'),
    
    # Matériaux
    path('materials/', views.material_list, name='material_list'),
    path('materials/create/', views.material_create, name='material_create'),
    path('materials/<int:pk>/update/', views.material_update, name='material_update'),
    path('materials/<int:pk>/delete/', views.material_delete, name='material_delete'),
    path('api/materials/', views.get_materials_for_machine, name='get_materials_for_machine'),
    path('public/machine/<int:machine_id>/<str:public_hash>/', views.public_machine_jobs, name='public_machine_jobs'),
] 