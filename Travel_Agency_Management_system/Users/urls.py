from django.urls import path

from Agency import context_processors
from . import views

urlpatterns = [
    path('users/', views.user_list, name='user_list'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('edit-permissions/<int:user_id>/', views.edit_permissions, name='user_permissions'),
    path('add-user/', views.user_register, name='user_register'),
    path('add-group/', views.create_group, name='create_group'),
    path('groups/', views.manage_groups, name='manage_groups'),
    path('groups/<int:group_id>/permissions/', views.edit_group_permissions, name='edit_group_permissions'),
    path('users/<int:user_id>/assign-groups/', views.assign_groups, name='assign_groups_to_user'),
    path('change-password',views.user_change_password,name='user_change_password'),
    path('change-user-password/<int:user_id>/',views.admin_change_user_password,name='admin_change_user_password'),
    path('', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('activity-log/', views.activity_log, name='activity_log'),


]