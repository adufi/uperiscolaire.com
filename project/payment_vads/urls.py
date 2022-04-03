from django.urls import path

from .views import *

urlpatterns = [
    path('paiement/vads/succes/', view=vads_success, name='vads_success'),
    path('paiement/vads/echec/', view=vads_error, name='vads_error'),

    path('api/payment/vads-ipn/', view=api_vads_ipn, name='api_vads_ipn'),
]

