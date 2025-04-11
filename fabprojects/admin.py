from django.contrib import admin
from .models import View, Section, Task, SubTask, Tag, CustomField, CustomFieldValue

# Configuration de l'admin pour les vues
@admin.register(View)
class ViewAdmin(admin.ModelAdmin):
    list_display = ('name', 'fablab', 'get_tasks_status', 'updated_at')
    list_filter = ('fablab',)
    search_fields = ('name', 'fablab__name')
    date_hierarchy = 'updated_at'

    def get_tasks_status(self, obj):
        total_tasks = Task.objects.filter(section__view=obj).count()
        completed_tasks = Task.objects.filter(section__view=obj, is_completed=True).count()
        if total_tasks == 0:
            return "Pas de tâches"
        return f"{completed_tasks}/{total_tasks} tâches complétées"
    get_tasks_status.short_description = 'Avancement'

# Configuration de l'admin pour les sections
@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'view', 'get_fablab', 'get_tasks_status')
    list_filter = ('view__fablab',)
    search_fields = ('name', 'view__name')
    ordering = ('view', 'order')

    def get_fablab(self, obj):
        return obj.view.fablab
    get_fablab.short_description = 'FabLab'

    def get_tasks_status(self, obj):
        total_tasks = obj.task_set.count()
        completed_tasks = obj.task_set.filter(is_completed=True).count()
        if total_tasks == 0:
            return "Pas de tâches"
        return f"{completed_tasks}/{total_tasks} tâches complétées"
    get_tasks_status.short_description = 'Avancement'

# Configuration de l'admin pour les tâches
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_view_and_section', 'get_fablab', 'deadline', 'is_completed', 'get_assigned_users')
    list_filter = ('section__view__fablab', 'is_completed', 'tags')
    search_fields = ('title', 'section__name', 'section__view__name')
    filter_horizontal = ('assigned_users', 'tags')
    ordering = ('deadline',)

    def get_view_and_section(self, obj):
        return f"{obj.section.view.name} > {obj.section.name}"
    get_view_and_section.short_description = 'Vue > Section'

    def get_fablab(self, obj):
        return obj.section.view.fablab
    get_fablab.short_description = 'FabLab'

    def get_assigned_users(self, obj):
        users = obj.assigned_users.all()
        if not users:
            return "Non assignée"
        return ", ".join([u.get_full_name() or u.username for u in users])
    get_assigned_users.short_description = 'Assignée à'

# Configuration de l'admin pour les sous-tâches
@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_task_info', 'get_fablab', 'is_completed')
    list_filter = ('task__section__view__fablab', 'is_completed')
    search_fields = ('title', 'task__title')
    ordering = ('task', 'order')

    def get_task_info(self, obj):
        return f"{obj.task.title} ({obj.task.section.view.name})"
    get_task_info.short_description = 'Tâche (Vue)'

    def get_fablab(self, obj):
        return obj.task.section.view.fablab
    get_fablab.short_description = 'FabLab'

# Configuration de l'admin pour les tags
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'fablab', 'color', 'get_tasks_count')
    list_filter = ('fablab',)
    search_fields = ('name', 'fablab__name')

    def get_tasks_count(self, obj):
        return obj.tasks.count()
    get_tasks_count.short_description = 'Nombre de tâches'

# Configuration de l'admin pour les champs personnalisés
@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'fablab', 'field_type', 'get_views_count')
    list_filter = ('fablab', 'field_type')
    search_fields = ('name', 'fablab__name')

    def get_views_count(self, obj):
        return obj.views.count()
    get_views_count.short_description = 'Nombre de vues'

# Configuration de l'admin pour les valeurs des champs personnalisés
@admin.register(CustomFieldValue)
class CustomFieldValueAdmin(admin.ModelAdmin):
    list_display = ('task', 'field', 'get_fablab', 'value')
    list_filter = ('field__fablab', 'field')
    search_fields = ('task__title', 'field__name', 'value')

    def get_fablab(self, obj):
        return obj.field.fablab
    get_fablab.short_description = 'FabLab'
