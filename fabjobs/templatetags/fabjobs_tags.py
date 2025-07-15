from django import template

register = template.Library()

@register.filter
def call(obj, arg):
    """Appelle une fonction avec un argument"""
    return obj(arg)

@register.filter
def status_color(status):
    """Retourne la classe de couleur Bootstrap en fonction du statut"""
    colors = {
        'completed': 'success',
        'in_progress': 'primary',
        'pending': 'warning',
        'cancelled': 'danger',
        'failed': 'danger'
    }
    return colors.get(status, 'secondary') 