from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'fabusers'

urlpatterns = [
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('register/', views.register, name='register'),
    path('register/invitation/<str:token>/', views.register_with_invitation, name='register_with_invitation'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='dashboard'), name='logout'),
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
    path('fablab-admin/', views.fablab_admin, name='fablab_admin'),
    path('fablab/<int:fablab_id>/delete/', views.delete_fablab, name='delete_fablab'),
    path('fablab/<int:fablab_id>/duplicate/', views.duplicate_fablab, name='duplicate_fablab'),
    path('fablab/<int:fablab_id>/update/', views.update_fablab, name='update_fablab'),
] 