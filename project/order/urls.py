from django.urls import path

from . import views


urlpatterns = [
    path('api/order/ipn/', views.api_order_ipn, name='api_order_ipn'),

    path('order/demo/', views.order_demo, name='order_demo'),
    path('order/print/<int:pk>/', views.order_print, name='order_print'),

    path('api/orders/', views.api_orders, name='api_orders'),
    path('api/orders/<int:pk>/', views.api_orders, name='api_orders'),

    path('api/tickets/', views.api_tickets, name='api_tickets'),

    # NotImplemented
    path('api/tickets/shop/<int:sy>/<int:child>/', views.api_tickets_shop, name='api_tickets_shop'),

    path('api/order/cancel/', views.api_cancel_order, name='api_cancel_order'),
    path('api/tickets/cancel/', views.api_cancel_tickets, name='api_cancel_tickets'),

    # Release 1.5.2
    path('api/order/verify/', views.api_order_verify, name='api_order_verify'),
    path('api/order/verify/soft/', views.api_order_verify_soft, name='api_order_verify_soft'),
    # path('api/order/create/', views.api_order_create, name='api_order_create'),

    # Release 1.5.4
    path('api/order/pay/instant/', views.api_order_pay_instant, name='api_order_pay_instant'),
    path('api/order/pay/<int:pk>/', views.api_order_pay, name='api_order_pay'),

    path('api/order/confirm/', views.api_order_confirm, name='api_order_confirm'),
    path('api/order/reserve/', views.api_order_reserve, name='api_order_reserve'),

    path('api/order/ipn/', views.api_order_ipn, name='api_order_ipn'),

    path('api/order/test/', views.api_order_test, name='api_order_test'),


    # Tmp
    # path('order/productsstocks/', views.products_stocks, name='products_stocks'),

    # Old
    # path('order/search', views.order_search, name='order_search'),
    # path('ticket/search', views.ticket_search, name='ticket_search'),

    # path('order/productsstocks/', views.products_stocks, name='products_stocks'),

    # Old
    # path('order/migration', views.order_migration, name='order_migration'),

    # path('order/verify', views.order_verify, name='order_verify'),
    # path('order/create', views.order_create, name='order_create'),
    # path('order/confirm', views.order_confirm, name='order_confirm'),

    # path('order/create/test', views.order_create_test, name='order_create_test'),

    # path('order/<int:pk>', views.order_id, name='order_id'),
    # path('order/date/<slug:date>', views.order_date, name='order_date'),

    # path('order/child/<int:pk>', views.order_child_id, name='order_child_id'),
]
