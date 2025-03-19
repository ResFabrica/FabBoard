from django import template
from django.db.models import QuerySet

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