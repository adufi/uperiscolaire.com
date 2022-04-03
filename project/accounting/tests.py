import json

from django.urls import reverse
from django.http.request import QueryDict
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status

from .models import Client, ClientCreditHistory, HistoryTypeEnum
from .serializers import ClientSerializers

from users.models import User, UserAuth, Role
from params.models import Product, SchoolYear
from registration.models import Sibling, SiblingChild


class BaseViewTest(APITestCase):
    client = APIClient()

    def setUp(self):
        return None


class BaseClientTests(BaseViewTest):

    def setUp(self):
        return None

    def test_create_client (self):
        Client.create(id=9998)
        Client.objects.create_client(id=9999)

        clients = Client.objects.filter(id__gte=9998, id__lte=9999)
        self.assertEqual(len(clients), 2)

    def test_set_client_credit (self):
        client = Client.create(id=9998)
        client.set_credit(10, 1, 1)
        client.set_credit(20, 1, 1)
        client.set_credit(30, 1, 1)
        client.set_credit(40, 1, 1)

        client.refresh_from_db()
        
        history = client.credit_history.all()
        
        self.assertEqual(client.credit, 40)
        self.assertEqual(len(history), 4)


class ClientGetAPITests(BaseViewTest):

    def setUp(self):
        # Roles
        self.r_adm = Role.objects.create(name='admin', slug='admin')
        self.r_par = Role.objects.create(name='parent', slug='parent')

        # Auths
        self.auth_admin = UserAuth.objects.create_auth(email='admin_client@mail.fr', password='password')
        self.auth_parent = UserAuth.objects.create_auth(email='parent_client@mail.fr', password='password')

        # Admin
        self.admin = User.objects.create()
        self.admin.roles.add(self.r_adm)
        self.admin.auth = self.auth_admin
        self.admin.save()

        # Parent
        self.parent = User.objects.create()
        self.parent.roles.add(self.r_par)
        self.parent.auth = self.auth_parent
        self.parent.save()

    """ Ensure access is forbidden for non proprietary object """
    def test_parent_forbidden_pk(self):
        r = self.client.get(
            reverse('api_clients', kwargs={'pk': 1}),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_parent.token}'
        )

        # print (r.json())
        data = r.json()

        self.assertEqual(data['message'], 'Vous n\'êtes pas autorisé a accéder à cette ressource.')

    """ Ensure an error is thrown if ressource does not exist """
    def test_parent_pk_not_found(self):
        Client.objects.create_client(id=9990)

        r = self.client.get(
            reverse('api_clients', kwargs={'pk': self.parent.id}),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_parent.token}'
        )

        # print (r.json())
        data = r.json()

        self.assertEqual(data['message'], 'Client introuvable.')

    """ """
    def test_parent_no_pk(self):
        Client.objects.create_client(id=self.parent.id)

        r = self.client.get(
            reverse('api_clients'),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_parent.token}'
        )

        # print (r.json())
        data = r.json()

        self.assertEqual(len(data['clients']), 1)
        self.assertEqual(data['clients'][0]['id'], self.parent.id)

    """ """
    def test_parent_with_pk(self):
        Client.objects.create_client(id=self.parent.id)

        r = self.client.get(
            reverse('api_clients', kwargs={'pk': self.parent.id}),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_parent.token}'
        )

        data = r.json()

        self.assertEqual(data['client']['id'], self.parent.id)

    """ TODO """
    def test_parent_with_pk_and_history(self):
        return None
        Client.objects.create_client(id=self.parent.id)

        r = self.client.get(
            reverse('api_clients', args=[f'{self.parent.id}/?history=True']),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_parent.token}'
        )

        data = r.json()

        self.assertTrue(data['client']['credit_history'])

    """ """
    def test_admin_pk_not_found(self):
        r = self.client.get(
            reverse('api_clients', kwargs={'pk': 1}),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_admin.token}'
        )

        data = r.json()

        self.assertEqual(data['message'], 'Client introuvable.')

    """ """
    def test_admin_with_pk(self):
        Client.objects.create_client(id=self.parent.id)

        r = self.client.get(
            reverse('api_clients', kwargs={'pk': self.parent.id}),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_admin.token}'
        )

        data = r.json()

        self.assertEqual(data['client']['id'], self.parent.id)

    """ """
    def test_admin_no_pk(self):
        Client.objects.create_client(id=self.admin.id)
        Client.objects.create_client(id=self.parent.id)

        r = self.client.get(
            reverse('api_clients'),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.auth_admin.token}'
        )

        # print (r.json())
        data = r.json()

        self.assertEqual(len(data['clients']['data']), 2)

