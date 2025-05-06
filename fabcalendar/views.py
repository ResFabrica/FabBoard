from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Q
from .models import CalendarEvent
from datetime import datetime, timedelta
import logging
from django.utils import timezone
import re
from fabusers.models import FabLab
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)

class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'fabcalendar/calendar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer le FabLab sélectionné depuis l'URL
        selected_fablab_id = self.request.GET.get('fablab')
        selected_fablab = None
        
        # Si un FabLab est sélectionné, vérifier que l'utilisateur y a accès
        if selected_fablab_id:
            try:
                selected_fablab = FabLab.objects.get(id=selected_fablab_id)
                if not self.request.user.is_superuser and selected_fablab not in self.request.user.fablabs.all():
                    logger.error(f"Utilisateur {self.request.user} n'a pas accès au FabLab {selected_fablab_id}")
                    selected_fablab = None
            except FabLab.DoesNotExist:
                logger.error(f"FabLab {selected_fablab_id} non trouvé")
                selected_fablab = None
        
        # Filtrer par les FabLabs de l'utilisateur
        fablabs = self.request.user.fablabs.all()
        if selected_fablab and self.request.user.is_superuser:
            fablabs = [selected_fablab]
        
        context['fablabs'] = fablabs
        context['selected_fablab'] = selected_fablab or fablabs.first()
        logger.info(f"FabLabs disponibles : {[f.id for f in fablabs]}")
        logger.info(f"FabLab sélectionné : {context['selected_fablab'].id if context['selected_fablab'] else None}")
        return context

def parse_date(date_str):
    """Parse une date au format FullCalendar en datetime aware."""
    try:
        # Gérer le format UTC (Z)
        if date_str.endswith('Z'):
            dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            return timezone.make_aware(dt)
        
        # Gérer le format avec offset (+/-HH:MM)
        if '+' in date_str or '-' in date_str:
            # Remplacer le format +02:00 par +0200 pour datetime.fromisoformat
            date_str = re.sub(r'(\+\d{2}):(\d{2})', r'\1\2', date_str)
            return timezone.make_aware(datetime.fromisoformat(date_str))
        
        # Format sans fuseau horaire
        dt = datetime.fromisoformat(date_str)
        return timezone.make_aware(dt)
        
    except ValueError as e:
        logger.error(f"Erreur de parsing de la date {date_str}: {e}")
        raise

def get_events(request):
    """Retourne les événements du calendrier au format JSON pour FullCalendar."""
    start = request.GET.get('start')
    end = request.GET.get('end')
    fablab_id = request.GET.get('fablab')
    
    logger.info(f"Recherche d'événements pour le FabLab {fablab_id} entre {start} et {end}")
    
    if not all([start, end, fablab_id]):
        logger.error(f"Paramètres manquants : start={start}, end={end}, fablab={fablab_id}")
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        start_date = parse_date(start)
        end_date = parse_date(end)
    except ValueError as e:
        logger.error(f"Format de date invalide: {e}")
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Vérifier que l'utilisateur a accès au FabLab
    try:
        fablab = FabLab.objects.get(id=fablab_id)
        if not request.user.is_superuser and fablab not in request.user.fablabs.all():
            logger.error(f"Utilisateur {request.user} n'a pas accès au FabLab {fablab_id}")
            return JsonResponse({'error': 'Access denied'}, status=403)
    except FabLab.DoesNotExist:
        logger.error(f"FabLab {fablab_id} non trouvé")
        return JsonResponse({'error': 'FabLab not found'}, status=404)
    
    # Récupérer les événements
    events = CalendarEvent.objects.filter(
        Q(fablab_id=fablab_id) &
        Q(start_date__gte=start_date) &
        Q(end_date__lte=end_date)
    )
    
    logger.info(f"Nombre d'événements trouvés : {events.count()}")
    
    # Formater les événements pour FullCalendar
    events_data = []
    for event in events:
        color = {
            'task': '#28a745',  # Vert pour les tâches
            'maintenance': '#dc3545',  # Rouge pour les maintenances
            'custom': '#007bff'  # Bleu pour les événements personnalisés
        }.get(event.event_type, '#6c757d')
        
        event_data = {
            'id': event.id,
            'title': event.title,
            'start': event.start_date.isoformat(),
            'end': event.end_date.isoformat(),
            'description': event.description,
            'type': event.event_type,
            'color': color,
            'url': f'/calendar/event/{event.id}/',  # URL pour voir les détails
            'allDay': event.allday  # Ajouter le champ allDay pour FullCalendar
        }
        events_data.append(event_data)
        logger.info(f"Événement ajouté : {event_data}")
    
    return JsonResponse(events_data, safe=False)

@login_required
def event_detail(request, event_id):
    """Vue détaillée d'un événement du calendrier."""
    event = get_object_or_404(CalendarEvent, id=event_id)
    
    # Vérifier que l'utilisateur a accès au FabLab de l'événement
    if not request.user.is_superuser and event.fablab not in request.user.fablabs.all():
        raise PermissionDenied
    
    # Récupérer l'objet lié (Task ou Maintenance)
    linked_object = None
    if event.content_type and event.object_id:
        try:
            linked_object = event.content_type.get_object_for_this_type(id=event.object_id)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'objet lié : {e}")
    
    context = {
        'event': event,
        'linked_object': linked_object,
        'fablab': event.fablab,
    }
    
    return render(request, 'fabcalendar/event_detail.html', context) 