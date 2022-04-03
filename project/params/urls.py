from django.urls import path
from . import views


urlpatterns = [
    # path('param/', views.get_param, name='param-latest'),
    # path('param/details/', views.get_param_details, name='param-details'),
    # path('param/<int:id>', views.get_param_by_id, name='param-id'),
    # path('params/', views.ListParamsView.as_view(), name='params'),

    path('params/', views.params, name='params'),
    path('params/all', views.params_all, name='params_all'),
    path('params/<int:id>', views.params_id, name='params_id'),
    path('params/details', views.params_details, name='params_details'),
    path('params/details/all', views.params_details_all, name='params_details_all'),
    path('params/details/<int:id>', views.params_details_id, name='params_details_id'),

    path('params/product/<int:id>', views.params_product_id, name='params_product_id'),


    # Release 1.0.4

    # Get active product/school year
    path('api/v2/product/active/', views.api_v2_product_active, name='api_v2_product_active'),
    path('api/v2/schoolyear/active/', views.api_v2_school_year_active, name='api_v2_school_year_active'),

    # Generic views for products/school years
    path('api/v2/schoolyears/', views.SchoolYearList.as_view(), name='api_v2_school_years_list'),
    path('api/v2/schoolyears/<int:pk>/', views.SchoolYearDetail.as_view(), name='api_v2_school_years_details'),

    path('api/v2/products/', views.ProductList.as_view(), name='api_v2_products_list'),
    path('api/v2/products/<int:pk>/', views.ProductDetail.as_view(), name='api_v2_products_details'),
]
