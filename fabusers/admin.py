from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import FabLab, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_fablab', 'get_accepts_contact', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__fablab', 'profile__accepts_contact')
    
    def get_fablab(self, obj):
        return obj.profile.fablab if hasattr(obj, 'profile') else None
    get_fablab.short_description = 'FabLab'
    get_fablab.admin_order_field = 'profile__fablab'
    
    def get_accepts_contact(self, obj):
        return obj.profile.accepts_contact if hasattr(obj, 'profile') else False
    get_accepts_contact.short_description = 'Accepte contact'
    get_accepts_contact.boolean = True
    get_accepts_contact.admin_order_field = 'profile__accepts_contact'

class FabLabAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'get_users_count', 'get_admins_count')
    search_fields = ('name', 'address')
    filter_horizontal = ('users', 'admins')
    
    def get_users_count(self, obj):
        return obj.users.count()
    get_users_count.short_description = 'Nombre d\'utilisateurs'
    
    def get_admins_count(self, obj):
        return obj.admins.count()
    get_admins_count.short_description = 'Nombre d\'administrateurs'

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'fablab', 'accepts_contact', 'last_activity')
    list_filter = ('fablab', 'accepts_contact')
    search_fields = ('user__username', 'user__email', 'phone')
    raw_id_fields = ('user', 'fablab')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(FabLab, FabLabAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
