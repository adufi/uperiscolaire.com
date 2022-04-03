"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# From develop branch
from django.contrib import admin
from django.urls import re_path, include
from django.conf import settings
from django.conf.urls.static import static

# From main branch
# from django.urls import path, include, re_path
# from django.contrib import admin
# from django.conf.urls.static import static

# from .settings.base import DEBUG, STATIC_URL, STATIC_ROOT, MEDIA_URL, MEDIA_ROOT

urlpatterns = [
    re_path('admin/', admin.site.urls),

    re_path('', include('acm.urls')),
    re_path('', include('order.urls')),
    re_path('', include('users.urls')),
    re_path('', include('client.urls')),
    re_path('', include('accounting.urls')),
    re_path('', include('client_intern.urls')),
    re_path('', include('registration.urls')),
    re_path('', include('payment_vads.urls')),

    re_path('', include('params.urls')),
    
    # re_path('(?P<version>(v1|v2))/', include('products.urls')),
]


if settings.DEBUG:
    # urlpatterns += static(STATIC_URL, document_root = STATIC_ROOT)
    # urlpatterns += static(MEDIA_URL, document_root = MEDIA_ROOT)

    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)