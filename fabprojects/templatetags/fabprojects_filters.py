from django import template
from django.db.models import QuerySet
import markdown as md

register = template.Library()

@register.filter
def filter_by_fablab(queryset, fablab):
    """Filtre un queryset par fablab."""
    if not queryset or not fablab:
        return queryset
    
    # Si c'est une liste d'objets, la convertir en queryset
    if isinstance(queryset, list):
        if not queryset:
            return queryset
        model = queryset[0].__class__
        queryset = model.objects.filter(pk__in=[obj.pk for obj in queryset])
    
    # Vérifier si l'objet a une relation directe avec fablab
    if hasattr(queryset.model, 'fablab'):
        return queryset.filter(fablab=fablab)
    
    # Vérifier les relations à travers d'autres modèles
    for field in queryset.model._meta.get_fields():
        if field.is_relation and hasattr(field.related_model, 'fablab'):
            # Construire le filtre en utilisant le nom du champ
            filter_name = f"{field.name}__fablab"
            return queryset.filter(**{filter_name: fablab})
    
    return queryset

@register.filter
def get_custom_field_value(task, field):
    """Récupère la valeur d'un champ personnalisé pour une tâche."""
    try:
        return task.custom_field_values.get(field=field)
    except:
        return None

@register.filter
def trim(value):
    """Supprime les espaces au début et à la fin d'une chaîne."""
    if value:
        return value.strip()
    return value

@register.filter
def split(value, separator):
    """Divise une chaîne selon un séparateur."""
    if value:
        return [item for item in value.split(separator) if item.strip()]
    return [] 

@register.filter
def markdown(value):
    """Convertit le texte en Markdown en HTML."""
    if not value:
        return ""
    return md.markdown(value, extensions=[
        'extra',
        'codehilite',
        'fenced_code',
        'tables',
        'nl2br',
        'sane_lists'
    ], output_format='html5')

@register.filter
def filter_tasks_by_view(tasks, view):
    """Filtre les tâches d'une vue spécifique et les trie par deadline."""
    if not tasks or not view:
        return []
    # Garde uniquement les tâches de la vue spécifiée
    view_tasks = [task for task in tasks if hasattr(task, 'section') and task.section and task.section.view_id == view.id]
    # Trier d'abord les tâches avec deadline, puis celles sans deadline (par date de création)
    tasks_with_deadline = [t for t in view_tasks if t.deadline]
    tasks_without_deadline = [t for t in view_tasks if not t.deadline]
    
    # Trier les tâches avec deadline
    sorted_tasks_with_deadline = sorted(tasks_with_deadline, key=lambda x: x.deadline)
    # Trier les tâches sans deadline par date de création décroissante
    sorted_tasks_without_deadline = sorted(tasks_without_deadline, key=lambda x: x.created_at, reverse=True)
    
    # Combiner les deux listes : d'abord les tâches avec deadline, puis celles sans deadline
    return sorted_tasks_with_deadline + sorted_tasks_without_deadline 