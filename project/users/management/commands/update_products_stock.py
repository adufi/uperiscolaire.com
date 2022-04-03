from datetime import datetime

from django.db.models import Q
from django.core.management.base import BaseCommand

from order.models import TicketStatus, StatusEnum
from params.models import Product

class Command(BaseCommand):
    help = 'Update products stock by tickets count'

    def seek (self, product_id):
        ts = TicketStatus.objects.filter(ticket__product=product_id).order_by('-ticket_id', '-date').distinct('ticket_id')

        count = 0
        for t in ts:
            if t.status in [StatusEnum.COMPLETED, StatusEnum.RESERVED, StatusEnum.WAITING]:
                count += 1

        return count

    def handle(self, *args, **kwargs):
        CATEGORIES = [
            # 4,          # MARS
            # 5,          # AVRIL
            # 6,          # MAI
            # 7,          # JUIN
            # 8,          # JUILLET
            # 9,          # AOUT
            # 16,         # CARNAVAL
            # 17,         # PAQUES
            18,         # GRDS_VACANCES_JUILLET
            19,         # GRDS_VACANCES_AOUT
        ]

        ps = Product.objects.filter(category__in=CATEGORIES, school_year__is_active=True)

        for p in ps:
            p.stock_current = self.seek(p.id)
            # print (f'{p.id} => {p.stock_current}')
            p.save()



    
