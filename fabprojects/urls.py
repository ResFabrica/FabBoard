from django.urls import path
from . import views

app_name = 'fabprojects'

urlpatterns = [
    # Vue principale des projets
    path('', views.project_home, name='home'),
    
    # Gestion des vues
    path('views/', views.view_list, name='view_list'),
    path('views/create/', views.view_create, name='view_create'),
    path('views/<int:view_id>/', views.view_detail, name='view_detail'),
    path('views/<int:view_id>/edit/', views.view_edit, name='view_edit'),
    path('views/<int:view_id>/delete/', views.view_delete, name='view_delete'),
    
    # Gestion des sections
    path('views/<int:view_id>/sections/create/', views.section_create, name='section_create'),
    path('sections/<int:section_id>/edit/', views.section_edit, name='section_edit'),
    path('sections/<int:section_id>/delete/', views.section_delete, name='section_delete'),
    path('sections/<int:section_id>/', views.section_detail, name='section_detail'),
    path('sections/<int:section_id>/update-tags/', views.section_update_tags, name='section_update_tags'),
    path('sections/<int:section_id>/move/', views.section_move, name='section_move'),
    
    # Gestion des tâches
    path('tasks/create/<int:section_id>/', views.task_create, name='task_create'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<int:task_id>/toggle-complete/', views.task_toggle_complete, name='task_toggle_complete'),
    path('tasks/<int:task_id>/move/', views.task_move, name='task_move'),
    path('task/<int:task_id>/update-users/', views.update_task_users, name='update_task_users'),
    
    # Gestion des sous-tâches
    path('tasks/<int:task_id>/subtasks/create/', views.subtask_create, name='subtask_create'),
    path('subtasks/<int:subtask_id>/edit/', views.subtask_edit, name='subtask_edit'),
    path('subtasks/<int:subtask_id>/delete/', views.subtask_delete, name='subtask_delete'),
    path('subtasks/<int:subtask_id>/complete/', views.subtask_toggle_complete, name='subtask_toggle_complete'),
    
    # Gestion des tags
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/create/', views.tag_create, name='tag_create'),
    path('tags/<int:tag_id>/edit/', views.tag_edit, name='tag_edit'),
    path('tags/<int:tag_id>/delete/', views.tag_delete, name='tag_delete'),
    path('tags/<int:tag_id>/tasks/', views.tag_tasks, name='tag_tasks'),
    path('tags/autocomplete/', views.tag_autocomplete, name='tag_autocomplete'),
    path('tags/check-exists/', views.check_tag_exists, name='check_tag_exists'),
    
    # Gestion des champs personnalisés
    path('custom-fields/', views.custom_field_list, name='custom_field_list'),
    path('custom-fields/create/', views.custom_field_create, name='custom_field_create'),
    path('custom-fields/<int:field_id>/edit/', views.custom_field_edit, name='custom_field_edit'),
    path('custom-fields/<int:field_id>/delete/', views.custom_field_delete, name='custom_field_delete'),
    path('custom-fields/json/', views.custom_field_list_json, name='custom_field_list_json'),
    path('custom-field/update/', views.update_custom_field, name='update_custom_field'),
    
    # Vues spéciales
    path('my-tasks/', views.my_tasks, name='my_tasks'),
    path('fablab-tasks/', views.fablab_tasks, name='fablab_tasks'),
    path('tasks/update-field/', views.update_task_field, name='update_task_field'),
    path('task-file/<int:file_id>/delete/', views.task_file_delete, name='task_file_delete'),
] 