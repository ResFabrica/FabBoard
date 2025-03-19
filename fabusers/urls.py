from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'fabusers'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('terms/', views.terms, name='terms'),
    path('fablabs/users/', views.fablab_users, name='fablab_users'),
    path('search/users/', views.search_users, name='search_users'),
    path('fablab/<int:fablab_id>/add-user/', views.add_user_to_fablab, name='add_user_to_fablab'),
    path('fablab/<int:fablab_id>/remove-user/<int:user_id>/', views.remove_user_from_fablab, name='remove_user_from_fablab'),
    path('toggle-staff/<int:user_id>/', views.toggle_staff, name='toggle_staff'),
    path('toggle-admin/<int:user_id>/', views.toggle_admin, name='toggle_admin'),
    path('fablab/<int:fablab_id>/toggle-fablab-admin/<int:user_id>/', views.toggle_fablab_admin, name='toggle_fablab_admin'),
    path('fablab/<int:fablab_id>/bulk-add-admin/', views.bulk_add_admin, name='bulk_add_admin'),
    path('fablab/<int:fablab_id>/bulk-remove-users/', views.bulk_remove_users, name='bulk_remove_users'),
    path('profile/update-avatar-color/', views.update_avatar_color, name='update_avatar_color'),
    path('register/invitation/<str:token>/', views.register_with_invitation, name='register_with_invitation'),
    path('fablab/<int:fablab_id>/generate-invitation/', views.generate_invitation_link, name='generate_invitation_link'),
] 