from datetime import datetime
from django.core.management.base import BaseCommand

from order.models import Order, OrderMethod, OrderStatus, Ticket, TicketStatus, MethodEnum, StatusEnum, Client, ClientCredit
from users.models import User, UserAuth, Role, UserEmail, UserPhone, UserAddress, UserEmailType
from params.models import Product, ProductStock, SchoolYear, CategoryEnum, SubCategoryEnum
from registration.models import Child, Sibling, SiblingChild, Record, CAF, Health, ChildPAI, ChildClass, ChildQuotient

from client_intern.utils import OrderHelper

class Command(BaseCommand):
    help = 'Report some products'

    def admin_report(self):

        # Order tickets by payer
        def sort (tickets):
            payers = {}
            
            for ticket in tickets:
                payer = ticket.order.payer
                if payer not in payers:
                    payers[payer] = []

                payers[payer].append(ticket)

            return payers

        # Report a set of tickets
        def report(payer, tickets):
            # print (f'payer: {payer}')
            # print (f'tickets: {len(tickets)}')
            
            # Get/Create client
            try:
                client = Client.objects.get(pk=payer)
            except Client.DoesNotExist:
                client = Client.objects.create(
                    id=payer,
                    user=payer
                )
                client.credit = ClientCredit.objects.create(client=client)
            
            amount = 0
            product_ids = {}

            # Get ticket price
            # 
            for ticket in tickets:
                if ticket.product not in product_ids:
                    product_ids[ticket.product] = 0
                
                else:
                    print (f'Duplicate product ({ticket.product}) with payee ({ticket.payee}) on ticket ({ticket.id})')
                    continue
                    
                status = ticket.status.first()
                if status.status == 2:
                    price = get_price(ticket)
                    print (f'price: {price}')

                    amount += price
                    # ticket.report()     
                
            print (f'amount: {amount}')
            # client.credit.update(amount)
            return client

        # Calculate price of a product
        # Tickets from migration doesnt have a valid price
        def get_price(ticket):
            try:
                user = User.objects.get(pk=ticket.payee)
                record = Child.objects.get(pk=ticket.payee).record
                product = Product.objects.get(pk=ticket.product)

                print (product.name)

            except User.DoesNotExist:
                print (f'User ({ticket.payee}) does not exist')
                return -1
            except Child.DoesNotExist:
                print (f'Child ({ticket.payee}) does not exist')
                return -1
            except Product.DoesNotExist:
                print (f'Product ({ticket.product}) does not exist')
                return -1

            # class_mod = check_classroom(product, record.classroom)
            if check_age(product, user.dob):
                return check_quotient(product, record.caf.q2)
            else:
                return product.price

        # Compare child dob with product date
        def check_age (product, dob):
            return False if OrderHelper.Verifications._get_age_from_date(dob, product.date) < 3 else True

        # Return a price by child quotient
        def check_quotient (product, quotient):
            if quotient == 1:
                return product.price
            elif quotient == 2:
                return product.price_q2
            elif quotient == 3:
                return product.price_q1

        # Useless...
        def check_classroom (product, classroom):
            if not classroom:
                return False
            age_range = 2
            if classroom >= 1 and classroom <= 4:
                age_range = 1

        # Macro 
        def fetch(tickets):
            print (len(tickets))
            payers = sort(tickets)
            for payer in payers:
                report(payer, payers[payer])

        fetch(Ticket.objects.filter(payee=2357, product__gte=90, product__lte=117))
        fetch(Ticket.objects.filter(payee=2357, product__gte=132, product__lte=159))


    def handle(self, *args, **kwargs):
        self.admin_report()


    
