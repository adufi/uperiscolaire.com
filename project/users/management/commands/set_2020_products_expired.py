from datetime import datetime

from django.db.models import Q
from django.core.management.base import BaseCommand

from params.models import Product

class Command(BaseCommand):
    help = 'Add date_end for 2020 products'

    def handle(self, *args, **kwargs):
        Product.objects.filter(
            Q(pk__in=[1001, 1002, 1003, 1004]) | 
            Q(pk__gte=1000, date__year=2020)
        ).update(date_end=datetime(2020, 12, 31))



    
