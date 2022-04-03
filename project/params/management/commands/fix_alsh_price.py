from datetime import datetime
from django.core.management.base import BaseCommand

from params.models import SchoolYear, Product, CategoryEnum, SubCategoryEnum


class Command(BaseCommand):
    help = 'Fix price of ALSH products'

    def handle(self, *args, **kwargs):
        ps = Product.objects.all()
        for p in ps:
            if p.category == 0 or p.category == 1:
                continue
            
            if p.subcategory == 1:
                p.price_q2 = 4.0
                p.price_q1 = 0.0

            elif p.subcategory == 2:
                p.price_q2 = 7.0
                p.price_q1 = 2.0

            p.save()