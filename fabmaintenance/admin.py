from django.contrib import admin
from .models import MachineType, Machine, MaintenanceType, Maintenance, MachineTemplate, MaintenanceTemplate
from fabusers.models import FabLab

class MachineInline(admin.TabularInline):
    model = Machine
    extra = 0

class MachineTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

class MachineAdmin(admin.ModelAdmin):
    list_display = ('name', 'fablab', 'machine_type', 'get_next_maintenance')
    list_filter = ('fablab', 'machine_type')
    search_fields = ('name', 'fablab__name')
    
    def get_next_maintenance(self, obj):
        next_maintenance = obj.maintenance_set.filter(completed_date__isnull=True).order_by('scheduled_date').first()
        if next_maintenance:
            return next_maintenance.scheduled_date
        return '-'
    get_next_maintenance.short_description = 'Prochaine maintenance'

class MaintenanceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'machine_type', 'period_days', 'is_custom')
    list_filter = ('machine_type', 'is_custom')
    search_fields = ('name',)

class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('get_machine_with_fablab', 'maintenance_type', 'scheduled_date', 'completed_date', 'scheduling_type')
    list_filter = ('machine__fablab', 'scheduling_type', 'completed_date')
    search_fields = ('machine__name', 'machine__fablab__name')
    date_hierarchy = 'scheduled_date'
    
    def get_machine_with_fablab(self, obj):
        return f"{obj.machine.name} ({obj.machine.fablab.name})"
    get_machine_with_fablab.short_description = 'Machine (FabLab)'

class MaintenanceTemplateInline(admin.TabularInline):
    model = MaintenanceTemplate
    extra = 1
    fields = ('name', 'period_days', 'priority', 'estimated_duration')

class MachineTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'manufacturer', 'model', 'machine_type')
    list_filter = ('machine_type', 'manufacturer')
    search_fields = ('name', 'manufacturer', 'model')
    inlines = [MaintenanceTemplateInline]

class MaintenanceTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'machine_template', 'period_days', 'priority', 'estimated_duration')
    list_filter = ('machine_template', 'priority')
    search_fields = ('name', 'machine_template__name')

admin.site.register(MachineType, MachineTypeAdmin)
admin.site.register(Machine, MachineAdmin)
admin.site.register(MaintenanceType, MaintenanceTypeAdmin)
admin.site.register(Maintenance, MaintenanceAdmin)
admin.site.register(MachineTemplate, MachineTemplateAdmin)
admin.site.register(MaintenanceTemplate, MaintenanceTemplateAdmin)
