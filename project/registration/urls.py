from django.urls import path
from . import views


urlpatterns = [
    # Release 1.4
    path('api/intel/', views.api_intel, name='api_intel'),
    path('api/intel/<int:pk>/', views.api_intel, name='api_intel'),



    path('siblings', views.siblings, name='siblings'),
    path('siblings/<int:pk>', views.siblings_id, name='siblings_id'),
    path('siblings/child/<int:pk>', views.siblings_child_id, name='siblings_child_id'),
    path('siblings/parent/<int:pk>', views.siblings_parent_id, name='siblings_parent_id'),
    
    path('families', views.families, name='families'),
    path('families/<int:pk>', views.families_id, name='families_id'),

    path('records', views.records, name='records'),
    path('records/<int:pk>', views.records_id, name='records_id'),
    path('records/child/<int:pk>', views.records_child_id, name='records_child_id'),
    
    # path('register/records', views.records, name='records'),
    # path('register/records/<int:pk>', views.records_id, name='records_id'),


    path('records/migration', views.records_migration, name='records_migration'),
    path('families/migration', views.families_migration, name='families_migration'),
    path('siblings/migration', views.siblings_migration, name='siblings_migration'),
]
