import json

from django.urls import reverse
from django.http.request import QueryDict
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status

from order.models import Order, OrderStatus, OrderMethod, Ticket, TicketStatus, StatusEnum, MethodEnum, OrderTypeEnum
from order.serializers import OrderSerializer

from users.models import User, UserAuth, Role
from params.models import Product, SchoolYear
from accounting.models import Client, ClientCreditHistory, HistoryTypeEnum as HTE
from registration.models import Sibling, SiblingChild, Record


""" User utils """
def create_user(email, first_name='', last_name='', role_slug=''):
    auth = UserAuth.objects.create(email=email, password='password')

    # Admin
    user = User.objects.create(
        first_name=first_name,
        last_name=last_name,
        auth=auth
    )
    user.roles.add(Role.objects.get(slug=role_slug))
    user.save()
    return user

def create_child(first_name='', last_name='', dob=''):
    user = User.objects.create(
        first_name=first_name,
        last_name=last_name,
        dob=dob
    )
    user.roles.add(Role.objects.get(slug='child'))
    user.save()
    return user

""" Sibling utils """
def create_sibling (parent_id, ):
    sibling = Sibling.objects.create(id=parent_id, parent=parent_id)
    sibling.add_intels({
        'quotient_1': 0,
        'quotient_2': 0,
        'recipent_number': 0,
    }, SchoolYear.objects.get(is_active=True))

    return sibling

""" Order utils """
def create_order(data):
    """
    Parameters
    ----------
    data -> dict {
        'payer': 0,
        'caster': 0,
        'amount': 0.0,
        'amount_rcvd': 0.0,

        'status': [],
        
        'methods': [{
            'amount': 0.0,
            'method': 0,
            'reference': '',
        }],

        'tickets': [{
            'payee': 0,
            'price': 0,
            'product': 0,
        }]
    }
    """
    order = Order.objects.create(
        payer=data['payer'],
        caster=data['caster'],
        amount=data['amount'],
        amount_rcvd=data.get('amount_rcvd', data['amount']),
    )

    for status in data['status']:
        order._add_status(status)
        
    # Methods
    if data['methods']:
        for method in data['methods']:
            OrderMethod.objects.create(
                amount=method['amount'],
                method=method['method'],
                reference=method['reference'],
                order=order
            )

    # Tickets
    for ticket in data['tickets']:
        _ = Ticket.objects.create(
            payee=ticket['payee'],
            price=ticket['price'],
            product=ticket['product'],
            order=order
        )

        for status in data['status']:
            _._add_status(status)

    return order

""" Params utils """
def create_product(name, sy, date=None, category=1, subcategory=0, price=0.0, price_q1=0.0, price_q2=0.0, stock_count=0, stock_max=0):
    product = Product.objects.create(
        name=name,
        date=date,
        category=category,
        subcategory=subcategory,
        price=price,
        price_q1=price_q1,
        price_q2=price_q2,
        school_year=sy,
        stock_max=stock_max,
        stock_current=stock_count,
    )
    return product

""" Accounting utils """
def create_client (pk, credit):
    client = Client.objects.create_client(pk)
    client.update_credit(credit, 0, 0)
    return client


class BaseViewTest(APITestCase):
    client = APIClient()

    def setUp(self):
        Role.objects.create(name='Admin', slug='admin')
        Role.objects.create(name='Child', slug='child')
        Role.objects.create(name='Parent', slug='parent')

        self.active_school_year = SchoolYear.objects.create(
            date_start='2000-01-01',
            date_end='2099-12-31',
            is_active=True
        )

        self.setUp_products()

        return None

    def setUp_products (self):
        self.septembre  = create_product(name='Septembre', price=20.0, sy=self.active_school_year)
        self.octobre    = create_product(name='Octobre', price=20.0, sy=self.active_school_year)
        self.novembre   = create_product(name='Novembre', price=20.0, sy=self.active_school_year)

        # Products - ALSH
        self.tous1 = create_product(name='Toussaint 1', sy=self.active_school_year, date='2019-10-10',
                                     category=14, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
        self.tous2 = create_product(name='Toussaint 2', sy=self.active_school_year, date='2019-10-11',
                                     category=14, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
        self.tous3 = create_product(name='Toussaint 3', sy=self.active_school_year, date='2019-10-12',
                                     category=14, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
        self.tous4 = create_product(name='Toussaint 4', sy=self.active_school_year, date='2019-10-13',
                                     category=14, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
        self.tous5 = create_product(name='Toussaint 5', sy=self.active_school_year, date='2019-10-14',
                                     category=14, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)

        self.noel1 = create_product(name='Noel 1', sy=self.active_school_year, date='2019-12-10',
                                     category=15, subcategory=2, price=20.0, price_q2=7.0, price_q1=2.0)
        self.noel2 = create_product(name='Noel 2', sy=self.active_school_year, date='2019-12-11',
                                     category=15, subcategory=2, price=20.0, price_q2=7.0, price_q1=2.0)
        self.noel3 = create_product(name='Noel 3', sy=self.active_school_year, date='2019-12-12',
                                     category=15, subcategory=2, price=20.0, price_q2=7.0, price_q1=2.0)
        self.noel4 = create_product(name='Noel 4', sy=self.active_school_year, date='2019-12-13',
                                     category=15, subcategory=2, price=20.0, price_q2=7.0, price_q1=2.0)
        self.noel5 = create_product(name='Noel 5', sy=self.active_school_year, date='2019-12-14',
                                     category=15, subcategory=2, price=20.0, price_q2=7.0, price_q1=2.0)

        self.aout1 = create_product(name='Aout 1', sy=self.active_school_year, date='2020-08-10',
                                     category=19, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
        self.aout2 = create_product(name='Aout 2', sy=self.active_school_year, date='2020-08-11',
                                     category=19, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
        self.aout3 = create_product(name='Aout 3', sy=self.active_school_year, date='2020-08-12',
                                     category=19, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
        self.aout4 = create_product(name='Aout 4', sy=self.active_school_year, date='2020-08-13',
                                     category=19, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
        self.aout5 = create_product(name='Aout 5', sy=self.active_school_year, date='2020-08-14',
                                     category=19, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)


