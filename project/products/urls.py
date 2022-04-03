from django.urls import path
from . import views


urlpatterns = [
    path('product/<int:id>', views.get_product, name="product"),
    path('products/', views.get_products, name="products"),
    path('products/all', views.get_products_all, name="products-all"),
]
