from django.apps import AppConfig


class FabcalendarConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fabcalendar'
    verbose_name = 'Calendrier'

    def ready(self):
        import fabcalendar.signals  # Import les signaux au démarrage de l'application 