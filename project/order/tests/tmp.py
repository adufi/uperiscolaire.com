import json

from django.urls import reverse
from django.http.request import QueryDict
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status

from .models import Client, ClientCredit, Order, OrderMethod, OrderStatus, Ticket, TicketStatus, StatusEnum
from .serializers import OrderSerializer

# from .utils import verify_order

from users.models import User, UserAuth, Role
from params.models import Product, SchoolYear
from registration.models import Sibling, SiblingChild

# tests for views


def create_ticket(order, payee, product, price, status):
    ticket = Ticket.objects.create(payee=payee, product=product, price=price, order=order)
    ticket._add_status(status=status)
    return ticket


class BaseViewTest(APITestCase):
    client = APIClient()

    @staticmethod
    def create_order(mode, status, name, amount, caster, parent, payment_order_uuid=0, description='', currency='EUR'):
        return Order.objects.create(
            mode=mode,
            status=status,
            name=name,
            description=description,
            amount=amount,
            currency=currency,
            caster=caster,
            parent=parent,
            payment_order_uuid=payment_order_uuid,
        )

    def setUp(self):
        # add test data
        return None


class CancelationTests(BaseViewTest):

    def setUp(self):
        # Roles
        self.r_adm = Role.objects.create(name='admin', slug='admin')
        self.r_par = Role.objects.create(name='parent', slug='parent')

        # Auths
        self.auth_admin = UserAuth.objects.create(email='admin_cancel@mail.fr', password='password')
        self.auth_payer = UserAuth.objects.create(email='parent_cancel@mail.fr', password='password')

        # Admin
        self.admin = User.objects.create()
        self.admin.roles.add(self.r_adm)
        self.admin.auth = self.auth_admin
        self.admin.save()

        # Payer/Parent
        self.payer = User.objects.create()
        self.payer.roles.add(self.r_par)
        self.payer.auth = self.auth_payer
        self.payer.save()

        self.payer_credit = Client.objects.create(id=self.payer.id, user=self.payer.id)
        self.payer_credit.credit = ClientCredit.objects.create(amount=0, client=self.payer_credit)
        self.payer_credit.save()

        # Children
        self.payee_1 = User.objects.create()

        # Siblings    
        self.payer_sibling = Sibling.objects.create(parent=self.payer.id)
        self.payer_sibling.add_child(self.payee_1.id)

        # Products
        sy = SchoolYear.objects.create(date_start='2020-01-01', date_end='2100-12-31')
        self.p1 = Product.objects.create(stock_current=100, school_year=sy)
        self.p2 = Product.objects.create(stock_current=100, school_year=sy)
        self.p3 = Product.objects.create(stock_current=100, school_year=sy)
        self.p4 = Product.objects.create(stock_current=100, school_year=sy)
        self.p5 = Product.objects.create(stock_current=100, school_year=sy)

    def test_permission_denied_for_parent(self):
        r = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_payer.token}'
        )

        # print (r.json())
        data = r.json()

        self.assertEqual(data['detail'], 'Vous n\'avez pas la permission d\'effectuer cette action.')
        
    def test_tickets_payer_has_no_sibling(self):
        self.payer_sibling.delete()

        response = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.payer.id,
                'tickets': [1, 2, 3]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_admin.token}'
        )

        data = response.json()
        # print (data)

        self.assertEqual(data['status'], 'Failure')
        self.assertIn('Famille introuvable', data['message'])

    def test_tickets_has_no_order(self):
        response = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.payer.id,
                'tickets': [1]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_admin.token}'
        )

        data = response.json()
        # print (data)

        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Reçu introuvable.')

    def test_tickets_order_doesnt_belong_to_payer(self):
        order = Order.objects.create(payer=77856)
        t1 = order.tickets.create(payee=self.payee_1.id)

        response = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.payer.id,
                'tickets': [t1.id]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_admin.token}'
        )

        data = response.json()
        # print (data)

        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Ce reçu n\'appartient pas à ce parent.')

    """ """
    def test_tickets_doesnt_belong_to_order(self):
        order = Order.objects.create(payer=self.payer.id)
        t1 = create_ticket(order, self.payee_1.id, 1, 10, StatusEnum.UNSET)

        response = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.payer.id,
                'tickets': [t1.id, 1]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_admin.token}'
        )

        data = response.json()
        # print (data)

        self.assertEqual(data['status'], 'Success')
        self.assertIn(f'Erreur: le ticket (1) n\'appartient pas à ce reçu.', data['cancel_status'][1])

    """ """
    def test_tickets_child_is_not_bound(self):
        order = Order.objects.create(payer=self.payer.id)
        t1 = create_ticket(order, self.payee_1.id, self.p1.id, 10, StatusEnum.UNSET)
        t2 = create_ticket(order, 74892, self.p1.pk, 10, StatusEnum.UNSET)

        response = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.payer.id,
                'tickets': [t1.id, t2.id]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_admin.token}'
        )

        data = response.json()
        # print (data)

        self.assertEqual(data['status'], 'Success')
        self.assertIn(f'Erreur: le ticket ({t2.id}) de l\'enfant ({t2.payee}) n\'est pas lié parent.', data['cancel_status'][1])

    """ """
    def test_tickets_product_does_not_exist(self):
        order = Order.objects.create(payer=self.payer.id)
        t1 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.COMPLETED)
        t2 = create_ticket(order, self.payee_1.id, self.p2.pk, 10, StatusEnum.COMPLETED)
        t3 = create_ticket(order, self.payee_1.id, self.p3.pk, 10, StatusEnum.COMPLETED)
        t4 = create_ticket(order, self.payee_1.id, self.p4.pk, 10, StatusEnum.COMPLETED)
        t5 = create_ticket(order, self.payee_1.id,       7885, 10, StatusEnum.UNSET)

        response = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.payer.id,
                'tickets': [t1.id, t2.id, t3.id, t4.id, t5.id]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_admin.token}'
        )

        data = response.json()
        # print (data)

        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['cancel_status'][4], f'Erreur: le produit (7885) du ticket ({t5.pk}) n\'existe pas.')

    """ Ensure canceled tickets are not credited """
    def test_tickets_canceled(self):
        order = Order.objects.create(payer=self.payer.id)
        
        t1 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.UNSET)
        t2 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.REPORTED)
        t3 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.REFUNDED)
        t4 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.CANCELED)

        response = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.payer.id,
                'tickets': [t1.id, t2.id, t3.id, t4.id]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_admin.token}'
        )

        data = response.json()
        # print (data)

        credit = ClientCredit.objects.get(pk=self.payer_credit.credit.id)

        self.assertEqual(data['status'], 'Success')
        self.assertEqual(credit.amount, 0)
        self.assertEqual(len(data['cancel_status']), 5)
        self.assertEqual(data['cancel_status'][3], f'Attention: le ticket ({t4.id}) a déjà été annulé, il ne sera pas crédité.')
    
    """ Ensure the order is canceled when every tickets are """
    def test_tickets_order_canceled(self):
        order = Order.objects.create(payer=self.payer.id)
        
        t1 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.UNSET)
        t2 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.REPORTED)
        t3 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.REFUNDED)
        t4 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.CANCELED)

        response = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.payer.id,
                'tickets': [t1.id, t2.id, t3.id, t4.id]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_admin.token}'
        )

        data = response.json()
        # print (data)

        credit = ClientCredit.objects.get(pk=self.payer_credit.credit.id)

        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['cancel_status'][4], f'Information: tous les tickets ont été annulé, ce reçu est annulé.')

    """ Ensure the given tickets are canceled """
    def test_tickets_works(self):
        order = Order.objects.create(payer=self.payer.id)
        
        t1 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.UNSET)
        t2 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.REPORTED)
        t3 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.REFUNDED)
        t4 = create_ticket(order, self.payee_1.id, self.p1.pk, 10, StatusEnum.CANCELED)
        t5 = create_ticket(order, self.payee_1.id, self.p2.pk, 10, StatusEnum.RESERVED)
        t6 = create_ticket(order, self.payee_1.id, self.p3.pk, 10, StatusEnum.COMPLETED)

        response = self.client.post(
            reverse('api_cancel_tickets'),
            json.dumps({
                'client': self.payer.id,
                'tickets': [t1.id, t2.id, t3.id, t4.id, t5.id, t6.id]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_admin.token}'
        )

        data = response.json()
        # print (data)

        credit = ClientCredit.objects.get(pk=self.payer_credit.credit.id)
        reserved = order.tickets.get(product=self.p2.pk).status.first()
        completed = order.tickets.get(product=self.p3.pk).status.first()

        self.assertEqual(data['status'], 'Success')
        self.assertEqual(credit.amount, 10)
        self.assertEqual(reserved.status, StatusEnum.CANCELED)
        self.assertEqual(completed.status, StatusEnum.CANCELED)



class OrderVerificationsTest(BaseViewTest):
    pass
     
"""
class OrderTest(BaseViewTest):
    # To test
    #     product stock
    #     5 items min. to be eligible to CAF
    #     PERI reductions per child
    #     eligibility for some products
             
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