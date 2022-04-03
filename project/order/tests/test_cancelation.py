import json

from unittest import skip

from django.urls import reverse
from django.http.request import QueryDict
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status

from . import BaseViewTest, create_user, create_child, create_order, create_client

from order.models import Order, OrderMethod, OrderStatus, Ticket, TicketStatus, StatusEnum, OrderTypeEnum, MethodEnum
from order.serializers import OrderSerializer

from accounting.models import Client

from order.utils import OrderHelper

from users.models import User, UserAuth, Role
from params.models import Product, SchoolYear
from registration.models import Sibling, SiblingChild, Record

# tests for views

def create_ticket(order, payee, product, price, status):
    ticket = Ticket.objects.create(payee=payee, product=product, price=price, order=order)
    ticket._add_status(status=status)
    return ticket


class CancelationTests(BaseViewTest):

    def setUp(self):
        super().setUp()

        self.admin = create_user(
            email='a@mail.fr', 
            last_name='TEST',
            first_name='Admin',
            role_slug='admin'
        )

        self.parent = create_user(
            email='p@mail.fr', 
            last_name='TEST',
            first_name='Parent',
            role_slug='parent'
        )

        self.child_1 = create_child(
            dob='2010-01-01',
            last_name='TEST',
            first_name='Child'
        )

        self.sibling = Sibling.objects.create(id=self.parent.id, parent=self.parent.id)
        self.sibling.add_intels({
            'quotient_1': 0,
            'quotient_2': 3,
            'recipent_number': 0,
        }, self.active_school_year.id)

        self.sibling.add_child(self.child_1.id)

        # Records
        Record.objects.create(
            child=self.child_1.id,
            classroom=1,
            school_year=self.active_school_year.id
        )

    def test_permission_denied_for_parent(self):
        r = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        data = r.json()

        self.assertEqual(r.status_code, 403)
        
        # self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Vous n\'êtes pas autorisé à consulter cette ressource.')

    #
    def test_key_error (self):
        res = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.parent.id
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()
        # print (data)

        self.assertEqual(res.status_code, 400)

        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Erreur clé \'tickets\'.')

    @skip
    # No 'tickets' in payload trigger 404
    def test_no_tickets (self):
        res = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.parent.id,
                'tickets': []
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()
        # print (data)

        self.assertEqual(res.status_code, 400)

        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Aucun reçu/ticket à annuler.')

    #
    def test_tickets_has_no_order(self):
        res = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.parent.id,
                'tickets': [1]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()
        # print (data)

        self.assertEqual(res.status_code, 404)

        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Reçu introuvable.')

    #
    def test_tickets_does_not_belong_to_payer(self):
        # print ('test_tickets_does_not_belong_to_payer')

        order = Order.objects.create(payer=77856)
        t1 = order.tickets.create(payee=self.child_1.id)

        res = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.parent.id,
                'tickets': [t1.id]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()
        # print (data)

        self.assertEqual(res.status_code, 403)

        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Ce reçu n\'appartient pas à ce parent.')

    """ """
    def test_tickets_doesnt_belong_to_order(self):
        # print ('test_tickets_doesnt_belong_to_order')

        order = Order.objects.create(payer=self.parent.id)
        t1 = create_ticket(order, self.child_1.id, 1, 10, StatusEnum.UNSET)

        order = Order.objects.create(payer=self.parent.id)
        t2 = create_ticket(order, self.child_1.id, 1, 10, StatusEnum.UNSET)

        res = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.parent.id,
                'tickets': [t1.id, t2.id]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()
        # print (data)

        self.assertEqual(res.status_code, 400)

        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], f'Le ticket ({t2.id}) n\'appartient pas à ce reçu.')

    #
    def test_cannot_credit_waiting_tickets (self):
        order = Order.objects.create(payer=self.parent.id)
        order._add_status(StatusEnum.WAITING)

        t1 = create_ticket(order, self.child_1.id, self.septembre.pk, 10, StatusEnum.WAITING)

        res = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.parent.id,
                'tickets': [t1.id]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()

        self.assertEqual(res.status_code, 400)

        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Impossible d\'annuler un ticket en attente.')

    """ """
    def test_cancel_order_does_not_exist(self):
        # print ('test_cancel_order_does_not_exist')

        order = Order.objects.create(payer=self.parent.id)
        order._add_status(StatusEnum.WAITING)

        t5 = create_ticket(order, self.child_1.id, 7885, 10, StatusEnum.WAITING)

        res = self.client.post(
            reverse('api_cancel_order'),
            json.dumps({
                'client': self.parent.id,
                'order_id': order.id
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()
        # print (data)

        self.assertEqual(res.status_code, 200)

        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['cancel_status'][0], f'Erreur: le produit (7885) du ticket ({t5.pk}) n\'existe pas.')

    """ """
    def test_credit_order_does_not_exist(self):
        order = Order.objects.create(payer=self.parent.id)
        order._add_status(StatusEnum.COMPLETED)

        t5 = create_ticket(order, self.child_1.id, 7885, 10, StatusEnum.COMPLETED)

        res = self.client.post(
            reverse('api_cancel_order'),
            json.dumps({
                'client': self.parent.id,
                'order_id': order.id
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()

        self.assertEqual(res.status_code, 200)

        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['cancel_status'][0], f'Erreur: le produit (7885) du ticket ({t5.pk}) n\'existe pas.')

    """ """
    def test_cancel_order(self):
        create_client(self.parent.id, 0)

        res = self.client.post(
            reverse('api_order_reserve'),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.tous1.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()

        self.assertEqual(res.status_code, 402)

        order = data['order']
        self.assertTrue(order)
        self.assertEqual(order['status'][0]['status'], StatusEnum.RESERVED)

        self.tous1.refresh_from_db()
        self.assertEqual(self.tous1.stock_current, 1)

        # Start cancelation
        res = self.client.post(
            reverse('api_cancel_order'),
            json.dumps({
                'client': self.parent.id,
                'order_id': order['id']
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()

        self.assertEqual(res.status_code, 200)

        self.assertEqual(data['status'], 'Success')

        order = Order.objects.get(pk=order['id'])

        last_status = order.status.first()
        self.assertEqual(last_status.status, StatusEnum.CANCELED)

        client = Client.objects.get(pk=self.parent.id)
        self.assertEqual(client.credit, 0)

        self.tous1.refresh_from_db()
        self.assertEqual(self.tous1.stock_current, 0)

    """ """
    def test_cancel_order_with_credit(self):
        # print ('test_cancel_order_with_credit')

        create_client(self.parent.id, 10)

        res = self.client.post(
            reverse('api_order_reserve'),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.tous1.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()

        self.assertEqual(res.status_code, 402)

        order = data['order']
        self.assertTrue(order)
        self.assertEqual(order['amount_rcvd'], 10.0)
        self.assertEqual(order['status'][0]['status'], StatusEnum.RESERVED)

        self.tous1.refresh_from_db()
        self.assertEqual(self.tous1.stock_current, 1)

        # Start cancelation
        res = self.client.post(
            reverse('api_cancel_order'),
            json.dumps({
                'client': self.parent.id,
                'order_id': order['id']
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()

        self.assertEqual(res.status_code, 200)

        self.assertEqual(data['status'], 'Success')

        order = Order.objects.get(pk=order['id'])

        last_status = order.status.first()
        self.assertEqual(last_status.status, StatusEnum.CREDITED)

        client = Client.objects.get(pk=self.parent.id)
        self.assertEqual(client.credit, 10.0)

        self.tous1.refresh_from_db()
        self.assertEqual(self.tous1.stock_current, 0)

    """ """
    def test_credit_order(self):
        # print ('test_credit_order')

        create_client(self.parent.id, 0)

        res = self.client.post(
            reverse('api_order_pay_instant'),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'methods': [{
                    'amount': 17.0,
                    'method': MethodEnum.CASH.value,
                    'reference': ''
                }],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.tous1.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()

        self.assertEqual(res.status_code, 201)

        order = data['order']
        self.assertTrue(order)
        self.assertEqual(order['status'][0]['status'], StatusEnum.COMPLETED)

        self.tous1.refresh_from_db()
        self.assertEqual(self.tous1.stock_current, 1)

        # Start cancelation
        res = self.client.post(
            reverse('api_cancel_order'),
            json.dumps({
                'client': self.parent.id,
                'order_id': order['id']
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()

        self.assertEqual(res.status_code, 200)

        self.assertEqual(data['status'], 'Success')

        order = Order.objects.get(pk=order['id'])

        last_status = order.status.first()
        self.assertEqual(last_status.status, StatusEnum.CREDITED)

        client = Client.objects.get(pk=self.parent.id)
        self.assertEqual(client.credit, 17.0)

        self.tous1.refresh_from_db()
        self.assertEqual(self.tous1.stock_current, 0)

    """ """
    def test_credit_ticket(self):
        # print ('test_credit_ticket')

        create_client(self.parent.id, 0)

        res = self.client.post(
            reverse('api_order_pay_instant'),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'methods': [{
                    'amount': 34.0,
                    'method': MethodEnum.CASH.value,
                    'reference': ''
                }],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.tous1.id,
                }, {
                    'children': [self.child_1.id],
                    'product': self.tous2.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()

        self.assertEqual(res.status_code, 201)

        order = data['order']
        self.assertTrue(order)
        self.assertEqual(order['status'][0]['status'], StatusEnum.COMPLETED)

        ticket = order['tickets'][0]

        self.tous1.refresh_from_db()
        self.assertEqual(self.tous1.stock_current, 1)

        # Start cancelation
        res = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.parent.id,
                'tickets': [ticket['id']]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()

        self.assertEqual(res.status_code, 200)

        self.assertEqual(data['status'], 'Success')

        order = Order.objects.get(pk=order['id'])
        ticket = order.tickets.first()

        last_status = order.status.first()
        self.assertEqual(last_status.status, StatusEnum.COMPLETED)

        last_status = ticket.status.first()
        self.assertEqual(last_status.status, StatusEnum.CREDITED)

        client = Client.objects.get(pk=self.parent.id)
        self.assertEqual(client.credit, 17.0)

        self.tous1.refresh_from_db()
        self.assertEqual(self.tous1.stock_current, 0)

    #
    def test_credit_every_tickets(self):
        # print ('test_credit_every_tickets')

        create_client(self.parent.id, 0)

        res = self.client.post(
            reverse('api_order_pay_instant'),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'methods': [{
                    'amount': 34.0,
                    'method': MethodEnum.CASH.value,
                    'reference': ''
                }],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.tous1.id,
                }, {
                    'children': [self.child_1.id],
                    'product': self.tous2.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()

        self.assertEqual(res.status_code, 201)

        order = data['order']
        self.assertTrue(order)
        self.assertEqual(order['status'][0]['status'], StatusEnum.COMPLETED)

        # self.tous1.refresh_from_db()
        # self.assertEqual(self.tous1.stock_current, 1)

        # self.tous2.refresh_from_db()
        # self.assertEqual(self.tous2.stock_current, 1)

        # Start cancelation
        res = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.parent.id,
                'tickets': [
                    order['tickets'][0]['id'],
                    order['tickets'][1]['id']
                ]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()

        self.assertEqual(res.status_code, 200)

        self.assertEqual(data['status'], 'Success')

        order = Order.objects.get(pk=order['id'])
        ticket = order.tickets.last()

        last_status = order.status.first()
        self.assertEqual(last_status.status, StatusEnum.CREDITED)

        last_status = ticket.status.first()
        self.assertEqual(last_status.status, StatusEnum.CREDITED)

        client = Client.objects.get(pk=self.parent.id)
        self.assertEqual(client.credit, 34.0)

        self.tous1.refresh_from_db()
        print (f'stock {self.tous1.stock_current}')
        self.assertEqual(self.tous1.stock_current, 0)



    """ """
    @skip
    def test_credit_order_does_not_exist(self):
        order = Order.objects.create(payer=self.parent.id)
        order._add_status(StatusEnum.COMPLETED)

        t5 = create_ticket(order, self.child_1.id, 7885, 10, StatusEnum.COMPLETED)

        res = self.client.post(
            reverse('api_cancel_order'),
            json.dumps({
                'client': self.parent.id,
                'order_id': order.id
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = res.json()

        self.assertEqual(res.status_code, 200)

        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['cancel_status'][0], f'Erreur: le produit (7885) du ticket ({t5.pk}) n\'existe pas.')

    """ Ensure canceled tickets are not credited """
    @skip
    def test_tickets_canceled(self):
        order = Order.objects.create(payer=self.parent.id)
        
        t1 = create_ticket(order, self.child_1.id, self.p1.pk, 10, StatusEnum.UNSET)
        t2 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.REPORTED)
        t3 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.REFUNDED)
        t4 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.CANCELED)

        response = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.parent.id,
                'tickets': [t1.id, t2.id, t3.id, t4.id]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = response.json()
        # print (data)

        credit = ClientCredit.objects.get(pk=self.parent.credit.id)

        self.assertEqual(data['status'], 'Success')
        self.assertEqual(credit.amount, 0)
        self.assertEqual(len(data['cancel_status']), 5)
        self.assertEqual(data['cancel_status'][3], f'Attention: le ticket ({t4.id}) a déjà été annulé, il ne sera pas crédité.')
    
    """ Ensure the order is canceled when every tickets are """
    @skip
    def test_tickets_order_canceled(self):
        order = Order.objects.create(payer=self.parent.id)
        
        t1 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.UNSET)
        t2 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.REPORTED)
        t3 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.REFUNDED)
        t4 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.CANCELED)

        response = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.parent.id,
                'tickets': [t1.id, t2.id, t3.id, t4.id]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = response.json()
        # print (data)

        credit = ClientCredit.objects.get(pk=self.parent.credit.id)

        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['cancel_status'][4], f'Information: tous les tickets ont été annulé, ce reçu est annulé.')
    
    """ Ensure the given tickets are canceled """
    @skip
    def test_tickets_works(self):
        order = Order.objects.create(payer=self.parent.id)
        
        t1 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.UNSET)
        t2 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.REPORTED)
        t3 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.REFUNDED)
        t4 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.CANCELED)
        t5 = create_ticket(order, self.payee_1.id, self.p2.pk, 10, StatusEnum.RESERVED)
        t6 = create_ticket(order, self.payee_1.id, self.p3.pk, 10, StatusEnum.COMPLETED)

        response = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.parent.id,
                'tickets': [t1.id, t2.id, t3.id, t4.id, t5.id, t6.id]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = response.json()
        # print (data)

        credit = ClientCredit.objects.get(pk=self.parent.credit.id)
        reserved = order.tickets.get(product=self.p2.pk).status.first()
        completed = order.tickets.get(product=self.p3.pk).status.first()

        self.assertEqual(data['status'], 'Success')
        self.assertEqual(credit.amount, 10)
        self.assertEqual(reserved.status, StatusEnum.CANCELED)
        self.assertEqual(completed.status, StatusEnum.CANCELED)


    @skip
    def test_tickets_payer_has_no_sibling(self):
        self.sibling.delete()

        response = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.parent.id,
                'tickets': [1, 2, 3]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = response.json()
        # print (data)

        self.assertEqual(data['status'], 'Failure')
        self.assertIn('Famille introuvable', data['message'])

    
    """ """
    @skip
    def test_tickets_child_is_not_bound(self):
        order = Order.objects.create(payer=self.parent.id)
        t1 = create_ticket(order, self.child_1.id, self.p1.id, 10, StatusEnum.UNSET)
        t2 = create_ticket(order, 74892, self.p1.pk, 10, StatusEnum.UNSET)

        response = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.parent.id,
                'tickets': [t1.id, t2.id]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = response.json()
        # print (data)

        self.assertEqual(data['status'], 'Success')
        self.assertIn(f'Erreur: le ticket ({t2.id}) de l\'enfant ({t2.payee}) n\'est pas lié parent.', data['cancel_status'][1])


"""


"""
"""
class OrderVerificationsTest(BaseViewTest):
    pass
   """  
"""
class OrderTest(BaseViewTest):
        To test
            product stock
            5 items min. to be eligible to CAF
            PERI reductions per child
            eligibility for some products
             
    create_payload = {
        'caster': 1,
        'parent': 17,
        'create_payload': {
            "peri": {
                "sept": {
                    "id": 77,
                    "children": [20, 21, 22] # 40
                },
                "octo": {
                    "id": 78,
                    "children": [21, 22, 23] # 40
                },
                "dece": {
                    "id": 79,
                    "children": [21, 20, 24] # 40
                },
                "janv": {
                    "id": 80,
                    "children": [20, 21, 23, 24, 25] # 60
                },
                "fevr": {
                    "id": 81,
                    "children": [24, 25] # 32
                }
            },
            "alsh": [
                {
                    "child_id": 20,
                    "categories": {
                        "noel": [85, 86, 87, 88, 89], # 85
                        # Wrong id - 6 plus
                        "tous": [90] # 0
                    }
                },
                {
                    "child_id": 21,
                    "categories": {
                        # Less than 5 items
                        "noel": [85, 86, 87], # 51
                        # Wrong id - 6 plus
                        "tous": [101] # 0
                    }
                },
                {
                    "child_id": 22,
                    "categories": {
                        # Wrong ids - minus 6
                        "paqu": [105, 106, 107], # 0 
                    }
                }
            ]
        }
    }

    confirm_payload = {
        'order_id': 1,
        'payment_id': 'fb16ffe6-88e3-4e50-baaa-16604def5e0f',

        # CASH = 2
        # CHECK = 3
        # ONLINE = 4
        'mode': 2,
    }

    create_payload_amount = 348

    def test_verify_order(self):
        verify_response = verify_order(self.create_payload)

        # print (verify_response)

        self.assertEqual(verify_response['status'], 'Success')
        self.assertEqual(verify_response['amount'], self.create_payload_amount)

    def test_verify_order_invalid_payload(self):
        verify_response = verify_order({})

        # print(verify_response)

        self.assertEqual(verify_response['status'], 'Failed')
        self.assertEqual(verify_response['message'], 'Wrong payload')

    def test_create_order(self):
        response = self.client.post(
            # 'http://localhost:8000/v1/order/create',
            reverse('create_order', kwargs={'version': 'v1'}),
            json.dumps(self.create_payload),
            content_type='application/json'
        )
        data = response.data
        # print (data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['name'], 'UPEEM - ALSH&PERI')
        self.assertEqual(data['description'], 'Paiement ALSH/PERI 2019-2020')
        self.assertEqual(data['amount'], self.create_payload_amount)

        order = Order.objects.get(id = data['order_id'])
        items = OrderItem.objects.filter(order=order.id)

        count = 0
        for item in data['items']:
            if not 'obs' in item:
                count += 1

        self.assertEqual(len(items), count)
        self.assertEqual(order.status, OrderStatus.PENDING)
        self.assertEqual(data['amount'], order.amount)

    def test_create_order_querydict(self):
        qd = QueryDict(
            json.dumps(self.cart)
        )

        response = self.client.post(
            # 'http://localhost:8000/v1/order/create',
            reverse('create_order', kwargs={'version': 'v1'}),
            qd,
            content_type='application/json'
        )
        data = response.data
        # print (data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['name'], 'UPEEM - ALSH&PERI')
        self.assertEqual(data['description'], 'Paiement ALSH/PERI 2019-2020')
        self.assertEqual(data['amount'], self.cart_amount)

        order = Order.objects.get(id = data['order_id'])
        items = OrderItem.objects.filter(order=order.id)

        count = 0
        for item in data['items']:
            if not 'obs' in item:
                count += 1

        self.assertEqual(len(items), count)
        self.assertEqual(order.status, OrderStatus.PENDING)
        self.assertEqual(data['amount'], order.amount)

    def test_create_order_invalid_payload(self):
        response = self.client.post(
            # 'http://localhost:8000/v1/order/create',
            reverse('create_order', kwargs={'version': 'v1'}),
            json.dumps({}),
            content_type='application/json'
        )
        data = response.data
        # print (data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['status'], 'Failed')
        self.assertEqual(data['message'], 'Wrong payload')

    def test_create_order_twice(self):
        print('test_create_order_twice')

        response = self.client.post(
            # 'http://localhost:8000/v1/order/create',
            reverse('create_order', kwargs={'version': 'v1'}),
            json.dumps(self.cart),
            content_type='application/json'
        )
        data = response.data

        id_1 = data['order_id']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['status'], 'Success')

        # 2nd iteration
        response = self.client.post(
            # 'http://localhost:8000/v1/order/create',
            reverse('create_order', kwargs={'version': 'v1'}),
            json.dumps(self.cart),
            content_type='application/json'
        )
        data = response.data

        # id_2 = data['order_id']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['status'], 'Success')
        self.assertEqual(id_1, data['order_id'])

    def test_confirm_order(self):
        o = Order.objects.create(amount=110, parent=1)

        self.confirm_payload['order_id'] = o.id
        self.confirm_payload['mode'] = OrderMode.CASH

        response = self.client.post(
            reverse('confirm_order', kwargs={'version': 'v1'}),
            json.dumps(self.confirm_payload),
            content_type='application/json'
        )

        data = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['status'], 'Success')
"""