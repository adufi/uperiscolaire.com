from django.urls import path

from . import views

app_name = 'client'

urlpatterns = [
    # Release 1.4
    path('', views.redirect_home, name='redirect_home'),
    path('accueil/', views.home, name='home'),

    # Login/Signup soon
    path('dev/login/', views.login, name='login'),

    # Accounting
    path('mon-profil/', views.user_dashboard_profile, name='user_dashboard_profile'),
    path('mon-profil/<int:pk>/', views.user_dashboard_profile, name='user_dashboard_profile'),

    # Shop/View
    # See acm.urls


    # path('v2/accueil/', views.home, name='home'),
    
    # path('v2/dashboard/profil/<int:pk>/', views.user_dashboard_profile, name='user_dashboard_profile'),
    path('v2/dashboard/famille/', views.user_dashboard_family, name='user_dashboard_family'),


    # New
    path('mngt/products/', views.mngt_products, name='mngt_products'),
]