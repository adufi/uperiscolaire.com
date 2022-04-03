from datetime import datetime
from django.core.management.base import BaseCommand

from order.models import Order, OrderMethod, OrderStatus, Ticket, TicketStatus, MethodEnum, StatusEnum, Client, ClientCredit
from params.models import Product


class Command(BaseCommand):
    help = 'Update products stocks from orders'

    def get_products (self):
        return Product.objects.filter(id__gte=1000)

    def get_tickets (self, products):
        for product in products:
            product.stock_current = self.get_tickets_by_product(product)
            product.save()

    def get_tickets_by_product (self, product):
        tickets = Ticket.objects.filter(product=product.id, status__status=StatusEnum.COMPLETED)
        return len(tickets)

    def handle(self, *args, **kwargs):
        products = self.get_products()

        self.get_tickets(products)
