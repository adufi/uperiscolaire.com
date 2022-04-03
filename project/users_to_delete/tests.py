import json

from django.urls import reverse
from django.http.request import QueryDict
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status

# from .utils import 
from .models import UserAuth, Role
from .serializers import UserSerializer
from .utils import _check_authorizations
from .utils_registers import _create_auth, create_user, create_client, create_parent

# Create your tests here.


class BaseTestView(APITestCase):
    client = APIClient()

    def create_role(self, name, slug):
        r = Role.objects.create(name=name, slug=slug)


    def create_user(self, first_name, last_name):
        u = User.objects.create(
            first_name=first_name,
            last_name=last_name
        )
        

    def setUp(self):
        self.create_role(name='Admin', slug='admin')
        self.create_role(name='Child', slug='child')
        self.create_role(name='Parent', slug='parent')
        self.create_role(name='Client', slug='client')
        self.create_role(name='AP admin', slug='ap_admin')
        return None


# class UserTests(BaseTestView):
#     def test_user

class BasicBehaviorTests(BaseTestView):
    _base_payload  = {
        'first_name': 'John',
        'last_name': 'Doe',
        'dob': '1990-04-17 0:0:0',
        'auth': {
            'email': 'johndoe@mail.fr',
            'password1': 'password',
            'password2': 'password'
        },
        'roles': [
            'child'
        ],
        'emails': [{
            'is_main': True,
            'email': 'johndoe@mail.fr',
            'type': 1
        }],
        'phones': [{
            'type': 3,
            'is_main': True,
            'phone': '0696123456'
        }],
        'address': [{
            'type': 1,
            'name': 'John',
            'is_main': True,
            'address1': '...',
            'address2': '',
            'zip_code': '97200',
            'city': 'Fort-de-France',
            'country': 'Martinique'
        }]
    }

    def test_jwt_encode_decode(self):
        a = _create_auth('user1@mail.fr', 'password')
        id = UserAuth.decode_auth_token(a.token)
        self.assertEqual(a.id, id)

    def test_create_user(self):
        payload = self._base_payload.copy()
        payload['roles'] = ['parent']
        user = create_user(payload)

        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.roles.all()[0].slug, 'parent')
        self.assertEqual(user.useremail_set.all()[0].email, 'johndoe@mail.fr')

    def test_create_parent(self):
        user = create_parent({
            'email': 'parent@mail.fr',
            'password1': 'password',
            'password2': 'password',
        })

        if type(user) is str:
            print(user)

        self.assertEqual(user.first_name, '')
        self.assertEqual(user.auth.email, 'parent@mail.fr')
        self.assertEqual(user.roles.all()[0].slug, 'parent')
        self.assertEqual(user.useremail_set.all()[0].email, 'parent@mail.fr')

    def test_create_client(self):
        payload = self._base_payload.copy()
        payload['auth']['email'] = 'johndoe@mail.fr'

        user_data = create_client(payload)

        self.assertEqual(user_data['first_name'], 'John')
        self.assertEqual(user_data['auth']['email'], 'johndoe@mail.fr')
        self.assertEqual(user_data['roles'][0]['slug'], 'client')
        self.assertEqual(user_data['emails'][0]['email'], 'johndoe@mail.fr')

    def test_check_authorization(self):
        payload = self._base_payload.copy()
        payload['roles'] = ['ap_admin']
        payload['auth']['email'] = 'ap_admin@mail.fr'
        ap_admin = create_user(payload)
        ap_admin.save()

        payload['roles'] = ['child']
        payload['auth']['email'] = 'child@mail.fr'
        child = create_user(payload)
        child.save()

        payload['roles'] = ['client']
        payload['auth']['email'] = 'client@mail.fr'
        client = create_user(payload)
        client.save()

        payload['roles'] = ['parent']
        payload['auth']['email'] = 'parent@mail.fr'
        parent = create_user(payload)
        parent.save()

        # Admin
        self.assertTrue(
            _check_authorizations(
                ap_admin.auth.token,
                ['admin', 'ap_admin']
            )
        )

        self.assertFalse(
            _check_authorizations(
                ap_admin.auth.token,
                ['client']
            )
        )

        # Child
        self.assertTrue(
            _check_authorizations(
                child.auth.token,
                ['child']
            )
        )

        self.assertFalse(
            _check_authorizations(
                child.auth.token,
                ['client']
            )
        )

        # Client
        self.assertTrue(
            _check_authorizations(
                client.auth.token,
                ['admin', 'client']
            )
        )

        self.assertFalse(
            _check_authorizations(
                client.auth.token,
                ['admin']
            )
        )

        # Parent
        self.assertTrue(
            _check_authorizations(
                parent.auth.token,
                ['client', 'parent']
            )
        )

        self.assertFalse(
            _check_authorizations(
                parent.auth.token,
                ['child']
            )
        )

    def test_check_authorization_invalid_token(self):
        self.assertFalse(
            _check_authorizations(
                'Hello World',
                ['admin']
            )
        )

        self.assertFalse(
            _check_authorizations(
                0,
                ['admin']
            )
        )


class AuthLoginTests(BaseTestView):

    def test_auth_login(self):
        a = _create_auth('admin@mail.fr', 'password')
        response = self.client.post(
            reverse('auth_login'),
            json.dumps({
                'email': 'admin@mail.fr',
                'password': 'password',
            }),
            content_type='application/json'
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['status'], 'Success')
        self.assertTrue(data['token'])

    def test_auth_login_invalid_payload(self):
        response = self.client.post(
            reverse('auth_login'),
            json.dumps({}),
            content_type='application/json'
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Invalid payload.')

    def test_auth_login_invalid_creadentials(self):
        response = self.client.post(
            reverse('auth_login'),
            json.dumps({
                'email': '',
                'password': '',
            }),
            content_type='application/json'
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Invalid credentials.')

"""
class AuthStatusTests(BaseTestView):
    def test_status(self):
        a = _create_auth('user1@mail.fr', 'password')
        
        response = self.client.post(
            reverse('auth_login'),
            json.dumps({
                'email': a.email,
                'password': 'password'
            }),
            content_type='application/json'
        )

        post_response = response.json()
        token = post_response['token']

        print (token)
        
        headers = { 'Authorization': f'Bearer: {token}' }

        response = self.client.get(
            reverse('auth_status'),
            Authorization=f'Bearer: {token}'
            # **headers
        )
        data = response.json()
        print (data['message'])

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['status'], 'Success')

    def test_status_invalid_token(self):
        headers = { 'Authorization': f'Bearer: Invalid token' }
        response = self.client.get(
            reverse('auth_status'),
            **headers
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Invalid token.')

    def test_status_invalid_payload(self):
        headers = { 'Authorization': '' }
        response = self.client.get(
            reverse('auth_status'),
            **headers
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Invalid payload.')
"""

class AuthRegisterTests(BaseTestView):
    def test_register(self):
        response = self.client.post(
            reverse('auth_register'),
            json.dumps({
                'email': 'user1@mail.fr',
                'password1': 'password',
                'password2': 'password',
            }),
            content_type='application/json'
        )
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['status'], 'Success')
        self.assertTrue(data['token'])
        self.assertTrue(data['user'])

    def test_register_different_passwords(self):
        response = self.client.post(
            reverse('auth_register'),
            json.dumps({
                'email': 'user1@mail.fr',
                'password1': 'password',
                'password2': 'password_',
            }),
            content_type='application/json'
        )
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['status'], 'Failure')
        self.assertIn('Passwords', data['message'])

    def test_register_invalid_payload(self):
        response = self.client.post(
            reverse('auth_register'),
            json.dumps({
                'email': 'user1@mail.fr',
                'password1': 'password',
            }),
            content_type='application/json'
        )
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['status'], 'Failure')
        self.assertIn('payload', data['message'])

    def test_register_same_email(self):
        self.client.post(
            reverse('auth_register'),
            json.dumps({
                'email': 'user1@mail.fr',
                'password1': 'password',
                'password2': 'password',
            }),
            content_type='application/json'
        )
        response = self.client.post(
            reverse('auth_register'),
            json.dumps({
                'email': 'user1@mail.fr',
                'password1': 'password',
                'password2': 'password',
            }),
            content_type='application/json'
        )
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['status'], 'Failure')
        self.assertIn('Email', data['message'])

"""
class UsersGetTests(BaseTestView):
    
    _base_payload = {
        'first_name': 'John',
        'last_name': 'Doe',
        'dob': '1990-04-17 0:0:0',
        'auth': {
            'email': 'johndoe@mail.fr',
            'password1': 'password',
            'password2': 'password'
        },
        'roles': [
            'child'
        ],
        'emails': [{
            'is_main': True,
            'email': 'johndoe@mail.fr',
            'type': 1
        }],
        'phones': [{
            'type': 3,
            'is_main': True,
            'phone': '0696123456'
        }],
        'address': [{
            'type': 1,
            'name': 'John',
            'is_main': True,
            'address1': '...',
            'address2': '',
            'zip_code': '97200',
            'city': 'Fort-de-France',
            'country': 'Martinique'
        }]
    }

    @property
    def _token(self):
        # user = create
        pass

    def test_get_users(self):
        self.create_user('John', 'Doe')
        self.create_user('Johnny', 'Doe')

        response = self.client.get(
            reverse('users'),
        )
        data = response.json()

        users = User.objects.all()
        users_serialier = UserSerializer(users, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['users'], users_serialier.data)

    def test_get_users_unauthorized(self):
        response = self.client.get(
            reverse('users_all')
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(data['status'], 'Failure')

    def test_get_clients(self):
        payload = self._base_payload.copy()
        payload['roles'] = ['client']
        user = create_user(payload)
        serializer = UserSerializer(user)

        response = self.client.get(
            reverse('users_clients')
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['users'][0], serializer.data)

    def test_get_children(self):
        payload = self._base_payload.copy()
        payload['roles'] = ['child']
        user = create_user(payload)
        serializer = UserSerializer(user)

        response = self.client.get(
            reverse('users_children')
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['users'][0], serializer.data)

    def test_get_parents(self):
        payload = self._base_payload.copy()
        payload['roles'] = ['parent']
        user = create_user(payload)
        serializer = UserSerializer(user)

        response = self.client.get(
            reverse('users_parents')
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['users'][0], serializer.data)
"""

class UsersPostTests(BaseTestView):

    def test_clients(self):
        # admin = User.objects.create()
        # admin_auth = UserAuth.objects.create_auth('admin@mail.fr', 'password')
        pass
