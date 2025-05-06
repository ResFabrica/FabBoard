from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta
from fabmaintenance.models import Maintenance
from fabprojects.models import Task, View
from fabusers.models import FabLab
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'
    
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
        
        # Récupérer les maintenances à venir
        if context['selected_fablab']:
            upcoming_maintenances = Maintenance.objects.filter(
                Q(machine__fablab=context['selected_fablab']) &
                Q(completed_date__isnull=True) &
                Q(scheduled_date__gte=timezone.now())
            ).order_by('scheduled_date')[:5]
            
            context['upcoming_maintenances'] = upcoming_maintenances
        
        # Récupérer les tâches en cours
        if context['selected_fablab']:
            current_tasks = Task.objects.filter(
                Q(section__view__fablab=context['selected_fablab']) &
                Q(assigned_users=self.request.user) &
                Q(is_completed=False)
            ).select_related(
                'section__view'
            ).order_by('deadline')
            
            context['current_tasks'] = current_tasks

        # Récupérer les vues de projet en cours
        if context['selected_fablab']:
            active_views = View.objects.filter(
                fablab=context['selected_fablab']
            ).order_by('-created_at')[:5]
            
            context['active_views'] = active_views
        
        return context 