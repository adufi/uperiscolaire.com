from django.urls import path

from . import views


urlpatterns = [
    path('api/clients/', views.api_clients, name='api_clients'),
    path('api/clients/<int:pk>/', views.api_clients, name='api_clients'),

    path('api/credithistory/<int:pk>/', views.api_credit_history, name='api_credit_history'),
]