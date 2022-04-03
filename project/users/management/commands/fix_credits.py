from datetime import datetime
from project.order.models import StatusEnum

from django.db.models import Q
from django.core.management.base import BaseCommand

from order.models import Order, StatusEnum, MethodEnum
from users.models import User
from params.models import Product
from accounting.models import Client, ClientCreditHistory

class Command(BaseCommand):
    help = 'Fix parent credits'

    def func_order (self, order):
        # Total amount customer paid
        amount_rcvd = 0
        # Amount paid with credit
        amount_credited = 0

        if order.status.filter(status=StatusEnum.COMPLETED):
            for ticket in order.tickets.all():
                status = ticket.status.first()
                if status.status == StatusEnum.CANCELED:


            # for method in order.methods.all():
            #     amount_rcvd += method.amount
            #     if method == MethodEnum.CREDIT:
            #         amount_credited += method.amount




    def run (self, parent):
        credit = 0
        credit_initial = 0

        orders = Order.objects.filter(payer=parent.id)

        for i, order in enumerate(orders):
            if i == 0:


    def handle(self, *args, **kwargs):
        parents = User.objects.filter(roles__slug='parent')

        for parent in parents:
            self.run (parent)


    
