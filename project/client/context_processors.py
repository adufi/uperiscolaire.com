import os

def site_antenna (request):
    return {
        'SITE_NAME': os.environ.get('DJANGO_SITE_NAME'),
        'BACKGROUND_NAME': os.environ.get('DJANGO_BACKGROUND_NAME'),
    }