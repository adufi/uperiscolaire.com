from django.urls import path
from rest_framework_jwt.views import obtain_jwt_token

from . import views

urlpatterns = [
    # path('token-auth/', obtain_jwt_token),

    # path('home', views.home, name='home'),

    path('auth/login/', views.auth_login, name='auth_login'),
    path('auth/status/', views.auth_status, name='auth_status'),
    path('auth/register/', views.auth_register, name='auth_register'),

    # path('users', views.users, name='users'),
    # path('users/search', views.users_search, name='users_search'),
    # path('users/<int:id>', views.users_id, name='users_id'),

    # path('users/payers/', views.users_payers, name='users_payers'),
    # path('users/clients/', views.users_clients, name='users_clients'),
    # path('users/parents/', views.users_parents, name='users_parents'),
    # path('users/children/', views.users_children, name='users_children'),

    # path('users/payers/migration', views.users_payers_migration, name='users_payers_migration'),
    # path('users/parents/migration', views.users_parents_migration, name='users_parents_migration'),
    # path('users/children/migration', views.users_children_migration, name='users_children_migration'),
]
