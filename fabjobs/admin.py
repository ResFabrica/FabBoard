from django.contrib import admin
from .models import Material, Job, JobFile

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'price_per_unit', 'co2_per_unit', 'get_fablabs')
    list_filter = ('unit', 'machine_types', 'fablabs')
    search_fields = ('name', 'description')
    filter_horizontal = ('machine_types', 'fablabs')

    def get_fablabs(self, obj):
        return ", ".join([fablab.name for fablab in obj.fablabs.all()])
    get_fablabs.short_description = "FabLabs"

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('name', 'machine', 'material', 'status', 'created_by', 'assigned_to', 'created_at')
    list_filter = ('status', 'machine__machine_type', 'machine__fablab', 'created_at')
    search_fields = ('name', 'description', 'notes')
    date_hierarchy = 'created_at'
    raw_id_fields = ('machine', 'material', 'created_by', 'assigned_to')

@admin.register(JobFile)
class JobFileAdmin(admin.ModelAdmin):
    list_display = ('job', 'file_type', 'description', 'uploaded_by', 'created_at')
    list_filter = ('file_type', 'job__status')
    search_fields = ('job__name', 'description')
    date_hierarchy = 'created_at'
    raw_id_fields = ('job', 'uploaded_by') 