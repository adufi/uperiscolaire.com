from django.urls import path

from . import views
from . import views_api

app_name = 'acm'

urlpatterns = [
    # Dev
    # path('resume-prestations-dev/', views.shop_summary_dev, name='shop_summary_dev'),
    # path('resume-prestations-dev/<int:pk>/', views.shop_summary_dev, name='shop_summary_dev'),

    path('resume-prestations/', views.shop_summary, name='shop_summary'),
    path('resume-prestations/<int:pk>/', views.shop_summary, name='shop_summary'),
    path('acheter-prestations/', views.shop_buy, name='shop_buy'),
    path('acheter-prestations/<int:pk>/', views.shop_buy, name='shop_buy'),
    path('consulter-prestations/', views.shop_view, name='shop_view'),
    path('consulter-prestations/<int:pk>/', views.shop_view, name='shop_view'),
    path('acheter-prestations/enfants/', views.shop_children, name='shop_children'),

    path('acheter-prestations/erreur/<int:pk>/', views.shop_cannot_buy, name='shop_cannot_buy'),
    
    path('api/shop/<int:pk>/', views_api.api_shop, name='api_shop'),
]