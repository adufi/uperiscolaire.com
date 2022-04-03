from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from . import views


urlpatterns = [
    # URGENT
    # path('alert', views.alert, name='alert'),

    # Release 1.4

    # Deprecated see in 'client'
    # path('', views.redirect_home, name='redirect_home'),
    # path('home/', views.home, name='home'),
    
    path('debug/', views.debug, name='debug'),

    path('login/', views.login, name='login'),
    path('intern/login/', views.login, name='login'),

    path('api/auth-token/', views.api_auth_token, name='api_auth_token'),

    path('change-password/', views.change_password, name='change_password'),
    path('change-password/<token>/', views.change_password, name='change_password'),
    path('password-forgotten/', views.password_forgotten, name='password_forgotten'),
    path('password-forgotten/<email>/', views.password_forgotten, name='password_forgotten'),

    path('verify/<token>/', views.verify_account, name='verify_account'),
    path('new-verification-link/<int:pk>/', views.new_verification_link, name='new_verification_link'),

    path('user/', views.user_user, name='user_user'),
    path('user/<int:pk>/', views.user_user, name='user_user'),
    path('family/<int:pk>/', views.user_family, name='user_familly'),
    path('record/<int:child>/', views.user_record, name='user_record'),
    path('record/<int:child>/<int:record>/', views.user_record, name='user_record'),
    path('record/<int:child>/<int:record>/pdf/', views.user_record_pdf, name='user_record_pdf'),
    path('record/<int:child>/<int:record>/print/', views.user_record_print, name='user_record_print'),

    # Shop
    path('acm/presta/view/<int:parent>/', views.shop_view, name='shop_view'),
    path('acm/presta/children/', views.shop_children, name='shop_children'),
    path('acm/presta/shop/<int:child>/', views.shop_shop_child, name='shop_shop_child'),
    path('acm/presta/summary/<int:child>/', views.shop_summary, name='shop_summary'),

    # Orders
    path('acm/orders/', views.orders, name='orders'),

    path('api/order/', views.api_order, name='api_order'),
    path('api/order/<int:pk>/', views.api_order, name='api_order'),

    # Admin - Management
    path('mngt/user/<int:pk>/', views.mngt_user, name='mngt_user'),
    path('mngt/users/', views.mngt_users, name='mngt_users'),
    
    # Regular route
    path('intern/user/', views.user_user, name='user_user'),
    path('intern/user/demo/', views.user_demo, name='user_demo'),
    path('intern/user/<int:pk>/', views.user_user, name='user_user'),
    path('intern/users/', views.user_users, name='user_users'),

    path('intern/record/', views.user_record, name='user_record'),
    path('intern/record/<int:child>/', views.user_record, name='user_record'),
    path('intern/record/<int:child>/<int:record>/', views.user_record, name='user_record'),
    # path('intern/record/<int:child>/<int:record>/print', views.user_record_print, name='user_record_print'),

    # path('intern/shop', views.shop, name='shop'),
    # path('intern/shop/shop', views.shop_shop, name='shop_shop'),


    # Params routes
    #
    #

    path('api/params/product/', views.api_params_product, name='api_params_product'),
    path('api/params/schoolyear/', views.api_params_schoolyear, name='api_params_schoolyear'),
    path('api/params/schoolyear/<int:pk>/', views.api_params_schoolyear, name='api_params_schoolyear'),


    # path('api/users/', views.api_users, name='api_users'),

    path('api/user/', views.api_user, name='api_user'),
    path('api/user/<int:pk>/', views.api_user, name='api_user'),
    path('api/user/names/', views.api_user_names, name='api_user_names'),
    path('api/userquery/', views.api_userquery, name='api_userquery'),

    path('api/sibling/', views.api_sibling, name='api_sibling'),
    path('api/sibling/<int:pk>/', views.api_sibling, name='api_sibling'),

    path('api/record/', views.api_record, name='api_record'),
    path('api/record/<int:pk>/', views.api_record, name='api_record'),

    path('api/user/intel/', views.api_user_intel, name='api_user_intel'),
    path('api/user/intel/<int:pk>/', views.api_user_intel, name='api_user_intel'),

    # User routes
    #
    #

    # Admin route - get user by id
    
    path('api/user/read/', views.api_user_read_profile, name='api_user_read_profile'),
    path('api/user/read/<int:pk>/', views.api_user_read_profile, name='api_user_read_profile'),
    path('api/users/read/', views.api_user_read_all, name='api_user_read_all'),

    path('api/user/update/', views.api_user_update, name='api_user_update'),
    path('api/user/child/create/', views.api_user_create_child, name='api_user_create_child'),
    path('api/user/child/delete/', views.api_user_delete_child, name='api_user_delete_child'),
    path('api/user/child/updatesibling/', views.api_user_update_sibling_child, name='api_user_update_sibling_child'),

    path('intern/shop/demo/', views.shop_demo, name='shop_demo'),
    path('intern/shop/children', views.shop_children, name='shop_children'),
    path('intern/shop/shop/<int:child>', views.shop_shop_child, name='shop_shop_child'),
    path('intern/shop/summary/<int:child>', views.shop_summary, name='shop_summary'),

    path('intern/orders', views.orders, name='orders'),
    path('intern/order/print/<int:pk>', views.order_print, name='order_print'),

    path('api/user/<int:id>', views.api_user_get, name='api_user_get'),
    # path('api/record/<int:id>', views.api_record_get, name='api_record_get'),

    path('api/order/<int:order>', views.api_order_get, name='api_order_get'),
    path('api/order/<int:order>/details', views.api_order_get_details, name='api_order_get_details'),
    path('api/order/date/<slug:date>', views.api_order_date, name='api_order_date'),

    # Release 1.5.2 - See order.urls
    # path('api/order/pay/', views.api_order_pay, name='api_order_pay'),
    # path('api/order/verify/', views.api_order_verify, name='api_order_verify'),
    # path('api/order/reserve/', views.api_order_reserve, name='api_order_reserve'),

    path('intern/users/<int:pk>', views.users_pk, name='users_pk'),
    path('intern/users/add', views.users_add, name='users_add'),

    path('intern/migration/orders', views.migration_orders, name='migration_orders'),

    path('migration/user', views.migration_user, name='migration_user'),
    path('migration/child', views.migration_child, name='migration_child'),
    path('migration/record', views.migration_record, name='migration_record'),
    path('migration/family', views.migration_family, name='migration_family'),
    path('migration/sibling', views.migration_sibling, name='migration_sibling'),

    path('migration/order', views.migration_order, name='migration_order'),
]

