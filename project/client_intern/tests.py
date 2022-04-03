import json

from django.urls import reverse
from django.http.request import QueryDict
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status

from order.models import OrderStock, Order, Ticket, OrderStatus, TicketStatus, OrderMethod, OrderTypeEnum, MethodEnum, StatusEnum, Client, ClientCredit
from order.serializers import OrderSerializer

from users.models import UserAuth, Role, User, UserPhoneType, UserEmailType, UserAddressType

from params.models import SchoolYear, Product, ProductStock

from registration.models import Family, Sibling, SiblingChild, SiblingIntels, Record, CAF, Health, ChildClass, ChildQuotient, ChildPAI

from .utils import UsersHelper, RegistrationHelper, OrderHelper, ParamsHelper, _check_authorizations

# tests for views



""" 
OrderVerificationsTest
"""
def _create_user(first_name, last_name, dob, _record=None):
    user = User.objects.create(
        first_name=first_name,
        last_name=last_name,
        dob=dob
    )

    if _record:
        c = Child.objects.create(id=user.id, user=user.id)
        # print (f'c.id = {c.id}')
        record = Record.objects.create(
            child=c,
            classroom=_record['classroom']
        )

        record.caf = CAF.objects.create(
            record=record,
            q1=_record['q1'],
            q2=_record['q2']
        )

        return {'user': user, 'record': record}

    return {'user': user}


def _create_sibling(parent, children):
    sibling = Sibling.objects.create(
        parent=parent
    )
    for child in children:
        # print (f'child = {child}')
        c = Child.objects.get(id=child)
        sibling.children.create(child=c)

    return sibling


def _create_product(name, sy, date=None, category=1, subcategory=0, price=0.0, price_q1=0.0, price_q2=0.0, stock_count=0, stock_max=0):
    product = Product.objects.create(
        name=name,
        date=date,
        category=category,
        subcategory=subcategory,
        price=price,
        price_q1=price_q1,
        price_q2=price_q2,
        school_year=sy
    )
    product.stock = ProductStock.objects.create(
        max=stock_max,
        count=stock_count,
        product=product
    )
    return product


def _create_ticket(payee, product, price, order):
    ticket = Ticket.objects.create(
        payee=payee,
        price=price,
        product=product,
        order=order
    )
    ticket.status.create(
        status=2
    )
    return ticket


def _alter_stock(product, _max, count=0):
    if not product.stock:
        product.stock = ProductStock.objects.create(
            max=_max,
            count=count,
            product=product
        )
        product.save()
    else:
        product.stock.max = _max
        product.stock.count = count    
        product.stock.save()
    return product.stock


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


class Authorizationstest(BaseViewTest):

    def setUp(self):
        self.r_adm = Role.objects.create(name='Admin', slug='admin')
        self.r_chi = Role.objects.create(name='Child', slug='child')
        self.r_par = Role.objects.create(name='Parent', slug='parent')

    def test_check_authorization(self):
        """
        Child is not supposed to authenticate
        """
        # print ('test_check_authorization')

        # Superuser
        user = User.objects.create()
        user.auth = UserAuth.objects.create_superuser(email='superuser@mail.fr', password='password')
        user.save()
        
        self.assertEqual(
            _check_authorizations(
                user.auth.token,
                ['is_superuser']
            ),
            {'role': 'is_superuser', 'id': user.id}
        )

        self.assertFalse(
            _check_authorizations(
                user.auth.token,
                ['admin']
            )
        )

        # Admin
        user = User.objects.create()
        user.roles.add(self.r_adm)
        user.auth = UserAuth.objects.create_user(email='admin@mail.fr', password='password')
        user.save()

        self.assertEqual(
            _check_authorizations(
                user.auth.token,
                ['admin', 'parent']
            ),    
            {'role': 'admin', 'id': user.id}
        )

        self.assertFalse(
            _check_authorizations(
                user.auth.token,
                ['parent', 'is_superuser']
            )
        )

        # Parent
        user = User.objects.create()
        user.roles.add(self.r_par)
        user.auth = UserAuth.objects.create_user(email='parent@mail.fr', password='password')
        user.save()

        self.assertEqual(
            _check_authorizations(
                user.auth.token,
                ['admin', 'parent']
            ),
            {'role': 'parent', 'id': user.id}
        )

        self.assertFalse(
            _check_authorizations(
                user.auth.token,
                ['admin', 'is_superuser']
            )
        )

        # User Authenticate
        self.assertTrue(
            _check_authorizations(
                user.auth.token,
                []
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


class RegistrationsTest(BaseViewTest):
    
    def setUp(self):
        self.r_adm = Role.objects.create(name='Admin', slug='admin')
        self.r_chi = Role.objects.create(name='Child', slug='child')
        self.r_par = Role.objects.create(name='Parent', slug='parent')

        _ = UserAuth.objects.create_superuser(email='superuser@mail.fr', password='password')
        self.superuser = User.objects.create(first_name='Super', last_name='User')
        self.superuser.auth = _
        self.superuser.save()

        _ = UserAuth.objects.create_user(email='admin@mail.fr', password='password')
        self.admin = User.objects.create(first_name='Admin', last_name='User')
        self.admin.auth = _
        self.admin.roles.add(self.r_adm)
        self.admin.save()

        _ = UserAuth.objects.create_user(email='parent@mail.fr', password='password')
        self.parent = User.objects.create(first_name='Parent', last_name='User')
        self.parent.auth = _
        self.parent.roles.add(self.r_par)
        self.parent.save()

        self.parent = UsersHelper.update_user({
            'id':           self.parent.id,
            'dob':          '1990-01-01',
            'first_name':   'Parent',
            'last_name':    'Test',
            'email':        'parent.test@mail.fr',
            'phone':        '0696987654',
            'address': {
                'city':         'Fort-de-France',
                'address1':     'Somewhere',
                'address2':     'Here',
                'zip_code':     '97200',
            }
        })

        self.sibling = Sibling.objects.create(parent=self.parent.id)
        self.sibling.add_intels({
            'recipent_number': 1
        }, school_year=1000)

        self.school_year = SchoolYear.objects.create(
            date_start='2019-01-01',
            date_end='2020-01-01',
            is_active=True
        )

    
    """ SiblingIntels """

    def test_intel_unauthorized_user(self):
        pass

    """ Ensure an error is thrown if a parent doesnt have a sibling """
    """ UPDATE: method doesnt matter """
    def test_intel_as_parent_no_sibling(self):
        self.sibling.delete()

        response = self.client.get(
            reverse('api_user_intel'),
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        data = response.json()

        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Sibling does not exist')

    """ Ensure a parent only get his intel """
    def test_get_intel_as_parent(self):
        response = self.client.get(
            reverse('api_user_intel', kwargs={'pk': self.sibling.intels.first().id}),
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        data = response.json()

        self.assertEqual(data['intel']['recipent_number'], 1)

    """ Ensure a parent get his intels """
    def test_get_intels_as_parent(self):
        self.sibling.add_intels({
            'recipent_number': 2
        }, school_year=2)

        sibling = Sibling.objects.create(parent=7864)
        sibling.add_intels({'recipent_number': 76878}, school_year=785)

        response = self.client.get(
            reverse('api_user_intel'),
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        data = response.json()

        self.assertTrue(data['intels'])
        self.assertEqual(len(data['intels']), 2)

    """ Ensure a parent can't access someone else intel """
    def test_get_intel_as_parent_unbound_pk(self):
        response = self.client.get(
            reverse('api_user_intel', kwargs={'pk': 79956546}),
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        data = response.json()

        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Intel is not bound to parent')

    """ Ensure an admin access an intel """
    def test_get_intel_as_admin(self):
        response = self.client.get(
            reverse('api_user_intel', kwargs={'pk': self.sibling.intels.first().id}),
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = response.json()

        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['intel']['recipent_number'], 1)

    """ Ensure an admin get the list of intels """
    def test_get_intels_as_admin(self):
        self.sibling.add_intels({
            'recipent_number': 2
        }, school_year=2)

        sibling = Sibling.objects.create(parent=7864)
        sibling.add_intels({'recipent_number': 76878}, school_year=785)

        response = self.client.get(
            reverse('api_user_intel'),
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = response.json()

        self.assertTrue(data['intels'])
        self.assertEqual(len(data['intels']), 3)


    """ Ensure an error is thrown if intel is not found """
    def test_get_intel_as_admin_invalid_pk(self):
        response = self.client.get(
            reverse('api_user_intel', kwargs={'pk': 5668}),
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = response.json()

        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Intel does not exist')


    """ Ensure an intel is created with active school year """
    def test_create_intel_as_parent(self):
        response = self.client.post(
            reverse('api_user_intel'),
            data=json.dumps({
                'recipent_number': 2,
                'insurance_policy': 2,
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        data = response.json()
        if 'message' in data:
            print (data['message'])
        intel = data['intel']

        self.assertEqual(data['status'], 'Success')

        response = self.client.get(
            reverse('api_user_intel', kwargs={'pk': intel['id']}),
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        data = response.json()

        self.assertEqual(data['intel']['id'], intel['id'])
        self.assertEqual(data['intel']['school_year'], self.school_year.id)


    """ Ensure quotients are ignored for parent """
    def test_create_intel_as_parent_with_quotient(self):
        response = self.client.post(
            reverse('api_user_intel'),
            data=json.dumps({
                'quotient_1': ChildQuotient.Q1,
                'quotient_2': ChildQuotient.Q1,

                'recipent_number': 2,
                'insurance_policy': 2,
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        data = response.json()
        intel = data['intel']

        self.assertEqual(data['status'], 'Success')

        response = self.client.get(
            reverse('api_user_intel', kwargs={'pk': intel['id']}),
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        data = response.json()

        self.assertEqual(data['intel']['id'], intel['id'])
        self.assertEqual(data['intel']['quotient_1'], ChildQuotient.UNSET)
        self.assertEqual(data['intel']['school_year'], self.school_year.id)


    """ Ensure registration is closed when no school year """
    def test_create_intel_as_parent_closed_registration(self):
        self.school_year.delete()
        
        response = self.client.post(
            reverse('api_user_intel'),
            data=json.dumps({
                'quotient_q1': ChildQuotient.Q1,
                'quotient_q2': ChildQuotient.Q1,

                'recipent_number': 2,
                'insurance_policy': 2,
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        data = response.json()

        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Registration closed for this period')

    
    """ Ensure an error is thrown if intel already exist """
    def test_create_intel_unicity(self):
        response = self.client.post(
            reverse('api_user_intel'),
            data=json.dumps({
                'recipent_number': 2,
                'insurance_policy': 2,
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        data = response.json()
        self.assertEqual(data['status'], 'Success')

        response = self.client.post(
            reverse('api_user_intel'),
            data=json.dumps({
                'recipent_number': 2,
                'insurance_policy': 2,
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        data = response.json()
        self.assertEqual(data['status'], 'Failure')


    """ """
    def test_create_intel_as_admin(self):
        response = self.client.post(
            reverse('api_user_intel'),
            data=json.dumps({
                'parent_id': self.parent.id,

                'recipent_number': 2,
                'insurance_policy': 2,
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = response.json()
        intel = data['intel']

        self.assertEqual(data['status'], 'Success')
        self.assertTrue(self.sibling.intels.filter(pk=intel['id']))


    """ """
    def test_create_intel_as_admin_no_parent_id(self):
        sibling = Sibling.objects.create(parent=self.admin.id)
        
        response = self.client.post(
            reverse('api_user_intel'),
            data=json.dumps({
                'recipent_number': 2,
                'insurance_policy': 2,
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = response.json()
        intel = data['intel']

        self.assertEqual(data['status'], 'Success')
        self.assertTrue(sibling.intels.filter(pk=intel['id']))


    """ """
    def test_create_intel_as_admin_with_quotient_school_year_verified(self):
        sy = SchoolYear.objects.create(
            date_start='2021-01-01',
            date_end='2022-01-01',
            is_active=False
        )

        response = self.client.post(
            reverse('api_user_intel'),
            data=json.dumps({
                'parent_id': self.parent.id,

                'quotient_1': ChildQuotient.Q1,
                'quotient_2': ChildQuotient.Q1,

                'recipent_number': 2,
                'insurance_policy': 2,

                'verified': True,
                'school_year': sy.id
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = response.json()
        # if 'message' in data:
        #     print (data['message'])

        self.assertEqual(data['status'], 'Success')
        self.assertTrue(data['intel']['date_verified'])
        self.assertEqual(data['intel']['quotient_1'], ChildQuotient.Q1)
        self.assertEqual(data['intel']['school_year'], sy.id)


    """ Ensure registration is closed when no school year """
    def test_create_intel_as_admin_closed_registration(self):
        self.school_year.delete()
        
        response = self.client.post(
            reverse('api_user_intel'),
            data=json.dumps({
                'parent_id': self.parent.id,

                'recipent_number': 2,
                'insurance_policy': 2,
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        data = response.json()

        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Registration closed for this period')


    """ """
    # def test_update_intel_as_parent(self):
    # def test_update_intel_as_parent_with_pk(self):
    # def test_update_intel_as_parent_with_pk_inactive(self):
    # def test_update_intel_as_parent_closed_registration(self):
    # def test_update_intel_as_parent_multiple_school_year(self):
    # def test_update_intel_as_parent_no_intel(self):
    # def test_update_intel_as_parent_multiple_intel(self):
    #     pass


class UsersHelperTest(BaseViewTest):
    """
    Full user payload {
        id                  - Optional
        last_name          
        first_name
        online_id           - Optional - default 0
        dob                 - Optional - Year-month-day hours:minutes:seconds
        is_active           - Optional - default True
        is_auto_password    - Optional - default False
        date_created?       - auto
        date_confirmed?     - auto
        
        auth                - Optional
            id              - Optional
            email
            password1
            password2

        roles []            
            role (slug)     - str
        
        phones              - Optional
            type
            phone
        
        emails []           - Optional
            is_main
            email
            type
        
        addresses           - Optional
            name
            type
            is_main
            address1
            address2
            zip_code
            city
            country
    }
    """

    def setUp(self):
        self.r_adm = Role.objects.create(name='Admin', slug='admin')
        self.r_chi = Role.objects.create(name='Child', slug='child')
        self.r_par = Role.objects.create(name='Parent', slug='parent')

        _ = UserAuth.objects.create_superuser(email='superuser@mail.fr', password='password')
        self.superuser = User.objects.create(first_name='Super', last_name='User')
        self.superuser.auth = _
        self.superuser.save()

        _ = UserAuth.objects.create_user(email='admin@mail.fr', password='password')
        self.admin = User.objects.create(first_name='Admin', last_name='User')
        self.admin.auth = _
        self.admin.save()

        self.parent = UsersHelper.register({
            'email':        'parent.test@mail.fr',
            'password1':    'password',
            'password2':    'password',
        })
        self.parent = UsersHelper.update_user({
            'id':           self.parent.id,
            'dob':          '1990-01-01',
            'first_name':   'Parent',
            'last_name':    'Test',
            'email':        'parent.test@mail.fr',
            'phone':        '0696987654',
            'address': {
                'city':         'Fort-de-France',
                'address1':     'Somewhere',
                'address2':     'Here',
                'zip_code':     '97200',
            }
        })


    """ User read """

    """ Ensure an user can access his profile """
    def test_read_profile(self):
        # print ('test_read_profile')

        response = self.client.get(
            reverse('api_user_read_profile'),
            HTTP_Authorization=f'Bearer {self.superuser.auth.token}'
        )

        data = response.json()

        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['user']['first_name'], 'Super')

    
    """ Ensure an user can access his profile with a pk """
    def test_read_profile_with_pk(self):
        # print ('test_read_profile_with_pk')

        response = self.client.get(
            reverse('api_user_read_profile', kwargs={'pk': self.parent.id}),
            HTTP_Authorization=f'Bearer {self.superuser.auth.token}'
        )

        data = response.json()

        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['user']['first_name'], 'Parent')


    """ Ensure a parent can access to his children data """
    def test_read_profile_parent_children(self):
        # print ('test_read_profile_unauthorized')

        child = User.objects.create(first_name='Child')
        sibling = Sibling.objects.create(parent=self.parent.id)
        sibling.add_child(child.id)

        response = self.client.get(
            reverse('api_user_read_profile', kwargs={'pk': child.id}),
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        data = response.json()

        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['user']['first_name'], 'Child')


    """ Ensure the server throw an error if pk is invalid """
    """ UPDATE: pk can't be negative - Ensure the server throw an error if pk is invalid """
    def test_read_profile_invalid_pk(self):
        # print ('test_read_profile_invalid_pk')

        response = self.client.get(
            reverse('api_user_read_profile', kwargs={'pk': 0}),
            HTTP_Authorization=f'Bearer {self.superuser.auth.token}'
        )

        data = response.json()

        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['user']['first_name'], 'Super')


    """ Ensure a parent can't access any user data """
    def test_read_profile_unauthorized(self):
        # print ('test_read_profile_unauthorized')$

        response = self.client.get(
            reverse('api_user_read_profile', kwargs={'pk': self.superuser.id}),
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        data = response.json()

        self.assertEqual(data['status'], 'Failure')
        self.assertIn('autorisé', data['message'])


    """ Parent creation """

    """ Ensure an user can create an account (as parent) """
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
        # print ('ok')

    """ Ensure an user can't create an account with different passwords """
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

    """ Ensure an user can't create an account with an invalid payload """
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

    """ Ensure an user can't create an account with an used email """
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

    """ """
    def test_register_password_too_short(self):
        response = self.client.post(
            reverse('auth_register'),
            json.dumps({
                'email': 'user1@mail.fr',
                'password1': 'short',
                'password2': 'short',
            }),
            content_type='application/json'
        )
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['status'], 'Failure')
        self.assertIn('short', data['message'])


    """ Parent migration """

    """ """
    def test_migration_parent(self):
        print ('test_migration_parent')
        parent = UsersHelper.migration_parent({
            'id':           5146,
            'first_name':   'Migration',
            'last_name':    'Test',
            'email':        'migration.test@mail.fr',
            'phone':        '0696987654',
            'address': {
                'city':         'Fort-de-France',
                'address1':     '',
                'address2':     '',
                'zip_code':     '97200',
            },
            'roles': ['admin']
        })

        if type(parent) is str:
            print (parent)

        role = parent.roles.first()
        phone = parent.phones.first()
        email = parent.emails.first()
        # address = parent.addresses.first()

        self.assertEqual(parent.id, 5146)
        self.assertEqual(parent.slug, 'testmigration')

        self.assertEqual(role.slug, 'parent')
        self.assertEqual(phone.phone, '0696987654')
        self.assertEqual(email.email, 'migration.test@mail.fr')

    """ """
    def test_migration_parent_invalid_payload(self):
        print ('test_migration_parent_invalid_payload')
        parent = UsersHelper.migration_parent({})
        # print (parent)
        self.assertIn('Invalid', parent)


    """ """
    def test_migration_parent_duplicate_slug(self):
        print ('test_migration_parent_duplicate_slug')
        UsersHelper.migration_parent({
            'id':           5146,
            'first_name':   'Migration',
            'last_name':    'Test',
            'email':        'migration.test@mail.fr',
            'phone':        '0696987654',
            'address': {
                'city':         'Fort-de-France',
                'address1':     '',
                'address2':     '',
                'zip_code':     '97200',
            },
            'roles': ['admin']
        })

        parent = UsersHelper.migration_parent({
            'id':           5147,
            'first_name':   'Migration',
            'last_name':    'Test',
            'email':        'migration.test@mail.fr',
            'phone':        '0696987654',
            'address': {
                'city':         'Fort-de-France',
                'address1':     '',
                'address2':     '',
                'zip_code':     '97200',
            },
            'roles': ['admin']
        })

        # print (parent)

        self.assertIn('Slug already exist', parent)
    

    """ """
    def test_migration_parent_duplicate_email(self):
        print ('test_migration_parent_duplicate_email')
        UsersHelper.migration_parent({
            'id':           5146,
            'first_name':   'Migration',
            'last_name':    'Test',
            'email':        'migration.test@mail.fr',
            'phone':        '0696987654',
            'address': {
                'city':         'Fort-de-France',
                'address1':     '',
                'address2':     '',
                'zip_code':     '97200',
            },
            'roles': ['admin']
        })

        parent = UsersHelper.migration_parent({
            'id':           5147,
            'first_name':   'Migration 2',
            'last_name':    'Test',
            'email':        'migration.test@mail.fr',
            'phone':        '0696987654',
            'address': {
                'city':         'Fort-de-France',
                'address1':     '',
                'address2':     '',
                'zip_code':     '97200',
            },
            'roles': ['admin']
        })

        # print (parent)

        self.assertIn('Email already exist', parent)
    

    """ Child creation """

    """ """
    def test_create_child (self):
        print ('test_create_child')
        # print (self.parent)
        response = self.client.post(
            reverse('api_user_create_child'),
            json.dumps({
                'parent_id': self.parent.id,
                'dob': '2020-01-01',
                'last_name': 'Test',
                'first_name': 'Child'
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer Hello'
            # Authorization=f'Bearer Hello'
        )
        data = response.json()
        # print (data)
        user = data['user']

        # Test user
        self.assertEqual(user['first_name'], 'Child')
        self.assertEqual(user['roles'][0]['slug'], 'child')

        # Test sibling
        sibling = Sibling.objects.get(parent=self.parent.id)
        self.assertTrue(sibling)
        self.assertTrue(sibling.children.get(child=user['id']))

        # Test family
        self.assertTrue(Family.objects.get(child=user['id'], parent=self.parent.id))


    """ """
    def test_create_child_invalid_payload (self):
        print ('test_create_child_invalid_payload')
        response = self.client.post(
            reverse('api_user_create_child'),
            json.dumps({}),
            content_type='application/json'
        )
        data = response.json()

        self.assertIn('Invalid payload', data['message'])
        self.assertEqual(data['status'], 'Failure')


    """ """
    def test_create_child_duplicate_slug(self):
        print ('test_create_child_duplicate_slug')
        # print (self.parent)
        response = self.client.post(
            reverse('api_user_create_child'),
            json.dumps({
                'parent_id': self.parent.id,
                'dob': '2020-01-01',
                'last_name': 'Test',
                'first_name': 'Child'
            }),
            content_type='application/json'
        )

        response = self.client.post(
            reverse('api_user_create_child'),
            json.dumps({
                'parent_id': self.parent.id,
                'dob': '2020-01-01',
                'last_name': 'Test',
                'first_name': 'Child'
            }),
            content_type='application/json'
        )

        data = response.json()
        # print (data)

        self.assertIn('Slug already exist', data['message'])
        self.assertEqual(data['status'], 'Failure')


    """ """
    def test_remove_child(self):
        print ('test_remove_child')
        # print (self.parent)
        response = self.client.post(
            reverse('api_user_create_child'),
            json.dumps({
                'parent_id': self.parent.id,
                'dob': '2020-01-01',
                'last_name': 'Test',
                'first_name': 'Child'
            }),
            content_type='application/json'
        )
        data = response.json()
        # print (data)

        self.assertTrue('user', data)
        user = data['user']

        response = self.client.post(
            reverse('api_user_delete_child'),
            json.dumps({
                'child': user['id']
            }),
            content_type='application/json'
        )

        user = User.objects.get(pk=user['id'])

        # Test user
        self.assertFalse(user.is_active)

        # Test sibling
        sibling = Sibling.objects.get(parent=self.parent.id)
        self.assertTrue(sibling)
        self.assertFalse(sibling.children.filter(child=user.id))

        # Test family
        self.assertFalse(Family.objects.filter(child=user.id, parent=self.parent.id))


    """ """
    def test_update_child_sibling(self):
        print ('test_update_child_sibling')
        # print (self.parent)
        response = self.client.post(
            reverse('api_user_create_child'),
            json.dumps({
                'parent_id': self.parent.id,
                'dob': '2020-01-01',
                'last_name': 'Test',
                'first_name': 'Child'
            }),
            content_type='application/json'
        )
        data = response.json()

        self.assertTrue('user', data)
        user = data['user']

        response = self.client.post(
            reverse('api_user_update_sibling_child'),
            json.dumps({
                'child_id': user['id'],
                'parent_id': 1000
            }),
            content_type='application/json'
        )

        data = response.json()
        # print (data)
        
        # Test sibling
        sibling = Sibling.objects.get(parent=self.parent.id)
        self.assertFalse(sibling.children.filter(child=user['id']))

        sibling = Sibling.objects.get(parent=1000)
        self.assertTrue(sibling)
        self.assertTrue(sibling.children.filter(child=user['id']))

        # Test family
        self.assertTrue(Family.objects.get(child=user['id'], parent=1000))


    """ """
    def test_update_child_sibling_delete_family(self):
        print ('test_update_child_sibling')
        # print (self.parent)
        response = self.client.post(
            reverse('api_user_create_child'),
            json.dumps({
                'parent_id': self.parent.id,
                'dob': '2020-01-01',
                'last_name': 'Test',
                'first_name': 'Child'
            }),
            content_type='application/json'
        )
        data = response.json()

        self.assertTrue('user', data)
        user = data['user']

        response = self.client.post(
            reverse('api_user_update_sibling_child'),
            json.dumps({
                'child_id': user['id'],
                'parent_id': 1000,
                'delete_family': True
            }),
            content_type='application/json'
        )

        data = response.json()
        # print (data)
        
        # Test sibling
        sibling = Sibling.objects.get(parent=self.parent.id)
        self.assertFalse(sibling.children.filter(child=user['id']))

        sibling = Sibling.objects.get(parent=1000)
        self.assertTrue(sibling)
        self.assertTrue(sibling.children.filter(child=user['id']))

        # Test family
        self.assertFalse(Family.objects.filter(child=user['id'], parent=self.parent.id))
        self.assertTrue(Family.objects.filter(child=user['id'], parent=1000))


    """ """
    def test_get_user(self):
        _ = User.objects.create(
            first_name='Foo',
            last_name='Test',
            dob='1990-01-01'
        )
        _.emails.create(
            email='foo@mail.fr',
            is_main=True,
            email_type=1
        )
        _.phones.create(
            phone='0696 12 34 56',
            is_main=True,
            phone_type=1
        )
        _.addresses.create(
            name='',
            is_main=True,
            address_type=1,
            address1='...',
            city='Fort-de-France',
            zip_code='97200',
            country='Martinique'
        )

        _user = UsersHelper.user_read(_.id)
        user = _user.to_json()
        self.assertEqual(user['first_name'], 'Foo')
        self.assertEqual(user['date_confirmed'], '')
        self.assertEqual(user['date_completed'], '')

        self.assertEqual(user['email'], 'foo@mail.fr')
        self.assertEqual(user['phone'], '0696 12 34 56')
        self.assertEqual(user['address']['address1'], '...')

    """ """
    def test_get_user_invalid_id(self):
        user = UsersHelper.user_read(1000000)
        self.assertFalse(user)

 
    """ """
    def test_update_user (self):
        _ = self.client.post(
            reverse('auth_register'),
            json.dumps({
                'email': 'test@mail.fr',
                'password1': 'password',
                'password2': 'password',
            }),
            content_type='application/json'
        )
        data = _.json()
        # print (data)

        response = self.client.post(
            reverse('api_user_update'),
            json.dumps({
                'id': data['user']['id'],
                'dob': '1990-01-01',
                'last_name': 'Test',
                'first_name': 'Foo',
                'email': 'test_@mail.fr',
                'phone': '0696 12 34 56',
                'address': {
                    'city': 'Fort-de-France',
                    'zip_code': '97200',
                    'address1': 'address 1',
                    'address2': 'address 2'
                }
            }),
            content_type='application/json'
        )
        # print (response.json())
        user = response.json()['user']

        # print (user)

        self.assertEqual(user['first_name'], 'Foo')
        self.assertTrue(user['date_completed'])


    
#     """ Ensure an user is created with minimal informations """
#     def test_base_create_basic_user(self):
#         # print('test_base_create_basic_user')
#         user = UsersHelper._users({
#             # 'id': 0,
#             'first_name': 'John',
#             'last_name': 'Doe',
#             # 'dob': '2019-01-01',
#             # 'online_id': 0,
#             # 'is_active': True,
#             # 'is_auto_password': False,

#             # 'auth': {
#             #     'email': 'john.doe@mail.fr',
#             #     'password1': 'password',
#             #     'password2': 'password'
#             # },

#             # 'roles': [
#             #     'parent'
#             # ],

#             # 'phones': [{
#             #     'type': UserPhoneType.HOME,
#             #     'phone': '0696123456'
#             # }],

#             # 'emails': [{
#             #     'is_main': True,
#             #     'email': 'john.doe@mail.fr',
#             #     'type': UserEmailType.HOME
#             # }],

#             # 'addresses': [{
#             #     'name': 'John\'s home',
#             #     'type': UserAddressType.HOME,
#             #     'is_main': True,
#             #     'address1': '...',
#             #     'address2': '...',
#             #     'zip_code': '97200',
#             #     'city': 'FdF',
#             #     'country': 'MQ'
#             # }],
#         })

#         # if type(user) is str:
#         #     print (user)

#         self.assertEqual(user.first_name, 'John')
#         self.assertEqual(user.last_name, 'Doe')
#         self.assertEqual(user.dob, None)
#         self.assertEqual(user.online_id, 0)
#         self.assertEqual(user.is_active, True)
#         self.assertEqual(user.is_auto_password, False)



#     """ Ensure an user is created with minimal informations """
#     def test_base_id_collision(self):
#         # print('test_base_id_collision')

#         UsersHelper._users({
#             'id': 1,
#             'first_name': '1',
#             'last_name': '1'
#         })
        
#         user = UsersHelper._users({
#             'first_name': '2',
#             'last_name': '2'
#         })
#         UsersHelper._users({
#             'id': 3,
#             'first_name': '3',
#             'last_name': '3'
#         })

#         # if type(user) is str:
#         #     print (user)

#         self.assertEqual(user.id, 2)

#     """ Ensure an user us created with full informations """
#     def test_base_create_user(self):
#         print('test_base_create_user')
#         user = UsersHelper._users({
#             'id': 1000,
#             'first_name': 'John',
#             'last_name': 'Doe',
#             'online_id': 500,
#             'dob': '2019-01-01',
#             'is_active': False,
#             'is_auto_password': True,

#             'auth': {
#                 'email': 'john.doe@mail.fr',
#                 'password1': 'password',
#                 'password2': 'password'
#             },

#             'roles': [
#                 'parent'
#             ],

#             'phones': [{
#                 'type': UserPhoneType.HOME,
#                 'phone': '0696123456'
#             }],

#             'emails': [{
#                 'is_main': True,
#                 'email': 'john.doe@mail.fr',
#                 'type': UserEmailType.HOME
#             }],

#             'addresses': [{
#                 'name': 'John\'s home',
#                 'type': UserAddressType.HOME,
#                 'is_main': True,
#                 'address1': '...',
#                 'address2': '...',
#                 'zip_code': '97200',
#                 'city': 'FdF',
#                 'country': 'MQ'
#             }],
#         })

#         # print (user)

#         auth = UserAuth.objects.last()
#         # print (auth)

#         if type(user) is str:
#             print(user)

#         self.assertEqual(user.id, 1000)
#         self.assertEqual(user.first_name, 'John')
#         self.assertEqual(user.last_name, 'Doe')
#         self.assertEqual(user.dob, '2019-01-01')
#         self.assertEqual(user.online_id, 500)
#         self.assertEqual(user.is_active, False)
#         self.assertEqual(user.is_auto_password, True)

#         self.assertEqual(user.auth.email, 'john.doe@mail.fr')

#         self.assertTrue(user.roles.get(slug='parent'))
#         self.assertTrue(user.phones.get(phone='0696123456'))
#         self.assertTrue(user.emails.get(email='john.doe@mail.fr'))
#         self.assertTrue(user.addresses.get(name='John\'s home'))

#     """ Ensure an user is created then updated """
#     """
#     def test_base_update_user(self):
#         print('test_base_update_user')

#         # 1st create the user
#         user = UsersHelper._users({
#             'id': 1001,
#             'first_name': 'John',
#             'last_name': 'Doe',
#             'online_id': 500,
#             'dob': '2019-01-01',
#             'is_active': False,
#             'is_auto_password': True,

#             'auth': {
#                 'email': 'john.doe@mail.fr',
#                 'password1': 'password',
#                 'password2': 'password'
#             },

#             'roles': [
#                 'parent'
#             ],

#             'phones': [{
#                 'type': UserPhoneType.HOME,
#                 'phone': '0696123456'
#             }],

#             'emails': [{
#                 'is_main': True,
#                 'email': 'john.doe@mail.fr',
#                 'type': UserEmailType.HOME
#             }],

#             'addresses': [{
#                 'name': 'John\'s home',
#                 'type': UserAddressType.HOME,
#                 'is_main': True,
#                 'address1': '...',
#                 'address2': '...',
#                 'zip_code': '97200',
#                 'city': 'FdF',
#                 'country': 'MQ'
#             }],
#         })

#         self.assertEqual(user.id, 1001)

#         # 2nd update this user
#         _user = UsersHelper._users({
#             'id': 1001,
#             'first_name': 'Johnny',
#             'last_name': 'Doe',
#             'online_id': 500,
#             'dob': '2019-01-01',
#             'is_active': False,
#             'is_auto_password': True,

#             'auth': {
#                 'id': user.auth.id,
#                 'email': 'johnny.doe@mail.fr',
#                 'password1': 'password',
#                 'password2': 'password'
#             },

#             'roles': [
#                 'admin'
#             ],

#             'phones': [{
#                 'type': UserPhoneType.HOME,
#                 'phone': '0696123456'
#             }],

#             'emails': [{
#                 'is_main': True,
#                 'email': 'john.doe@mail.fr',
#                 'type': UserEmailType.HOME
#             }],

#             'addresses': [{
#                 'name': 'John\'s home',
#                 'type': UserAddressType.HOME,
#                 'is_main': True,
#                 'address1': '...',
#                 'address2': '...',
#                 'zip_code': '97200',
#                 'city': 'FdF',
#                 'country': 'MQ'
#             }],
#         })

#         if type(_user) is str:
#             print(_user)

#         self.assertEqual(_user.first_name, 'Johnny')
#         self.assertEqual(_user.auth.email, 'johnny.doe@mail.fr')
#         self.assertTrue(_user.roles.get(slug='admin'))
#     """


# class RegistrationHelperTest(BaseViewTest):

#     def setUp(self):
#         pass

#     """ """
#     def test_create_record(self):
#         r = RegistrationHelper.create_record(50, {
#             'school': 'HM',
#             'classroom': ChildClass.SM,
#             'caf': {
#                 'q1': ChildQuotient.Q2,
#                 'q2': ChildQuotient.Q2,
#                 'recipent_number': '0'
#             },
#             'health': {
#                 'asthme': True,
#                 'allergy_food': True,
#                 'allergy_drug': True,
#                 'allergy_food_details': '...', 
#                 'allergy_drug_details': '...',
#                 'pai': ChildPAI.YES
#             }
#         })

#         # if type(r) is str:
#             # print(r)

#         self.assertEqual(r.school, 'HM')
#         self.assertEqual(r.classroom, ChildClass.SM)

#         self.assertEqual(r.caf.q2, ChildQuotient.Q2)
#         self.assertEqual(r.health.asthme, True)

#     """ """
#     def test_update_record(self):
#         _r = RegistrationHelper.create_record(50, {
#             'school': 'HM',
#             'classroom': ChildClass.SM,
#             'caf': {
#                 'q1': ChildQuotient.Q2,
#                 'q2': ChildQuotient.Q2,
#                 'recipent_number': '0'
#             },
#             'health': {
#                 'asthme': True,
#                 'allergy_food': True,
#                 'allergy_drug': True,
#                 'allergy_food_details': '...', 
#                 'allergy_drug_details': '...',
#                 'pai': ChildPAI.YES
#             }
#         })

#         r = RegistrationHelper.update_record(50, {
#             'id': _r.id,
#             'school': 'HM',
#             'classroom': ChildClass.CP,
#             'caf': {
#                 'q1': ChildQuotient.Q1,
#                 'q2': ChildQuotient.Q2,
#                 'recipent_number': '0'
#             },
#             'health': {
#                 'asthme': False,
#                 'allergy_food': True,
#                 'allergy_drug': True,
#                 'allergy_food_details': '...',
#                 'allergy_drug_details': '...',
#                 'pai': ChildPAI.YES
#             }
#         })

#         # if type(r) is str:
#             # print(r)

#         self.assertEqual(r.id, _r.id)
#         self.assertEqual(r.classroom, ChildClass.CP)
#         self.assertEqual(r.caf.q1, ChildQuotient.Q1)
#         self.assertEqual(r.health.asthme, False)

#     """ """
#     def test_create_family(self):
#         c = RegistrationHelper.Child.create(50)
#         r = RegistrationHelper.Family.create(c, 51)

#         if type(r) is str:
#             print(r)

#         self.assertEqual(r.parent, 51)
#         self.assertEqual(r.child.id, 50)

#     """ """
#     def test_create_sibling(self):
#         RegistrationHelper.Child.create(50)
#         RegistrationHelper.Child.create(51)
#         RegistrationHelper.Child.create(52)

#         r = RegistrationHelper.Sibling.create({
#             'parent': 49,
#             'children': [50, 51, 52]
#         })

#         if type(r) is str:
#             print(r)

#         self.assertEqual(r.parent, 49)
#         self.assertEqual(r.children.count(), 3)


# class OrderTest(BaseViewTest):

#     def setUp(self):
#         pass

#     def test_order_create(self):
#         pass

#     def test_order_update(self):
#         pass


# """ Test orders verification process """
# class OrderVerificationsTest(BaseViewTest): 

#     """ 
#     Parent 1 is bind 

#     """
#     def setUp(self):
#         """ Macros """
#         def macro_create_child(dob, q1, q2, cl):
#             tmp = _create_user(
#                 '', '', dob,
#                 {
#                     'q1': q1,
#                     'q2': q2,
#                     'classroom': cl
#                 }
#             )
#             return tmp['user'], tmp['record']

#         """ Main """

#         # Parent 1
#         self.p1 = _create_user('', '', None)['user']

#         # Child 1 - Bind
#         self.c1, self.r1 = macro_create_child('2017-06-01', 1, 2, 1) 

#         # Child 2 - Bind
#         self.c2, self.r2 = macro_create_child('2015-03-01', 2, 3, 1) 

#         # Child 3 - Bind
#         self.c3, self.r3 = macro_create_child('2014-03-01', 3, 1, 5)

#         # Child 4 - Bind
#         self.c4, self.r4 = macro_create_child('2013-03-01', 1, 3, 6)

#         # Child 5 - Bind
#         # Classroom set to 0 for test_alsh_classroom_not_set 
#         self.c5, self.r5 = macro_create_child('2012-03-01', 2, 1, 0)

#         # Sibling
#         Child.objects.create(id=100000, user=100000)
#         # print ('USER: {}'.format(Child.objects.get(id=100000).user))
#         self.sibling = _create_sibling(
#             self.p1.id,
#             [
#                 self.c1.id,
#                 self.c2.id,
#                 self.c3.id,
#                 self.c4.id,
#                 self.c5.id,
#                 100000 # Fake ID - ALSH bound but don't exist
#             ]
#         )

#         # Parent 2 - No bound children
#         self.p2 = _create_user('', '', None)['user']

#         # Child 10 - No sibling
#         self.c10, self.r10 = macro_create_child(None, 0, 0, 0)

#         # Products
#         sy = SchoolYear.objects.create(date_start='2019-09-01', date_end='2020-08-30')

#         # Products - PERI
#         self.septembre  = _create_product(name='Septembre', price=20.0, sy=sy)
#         self.octobre    = _create_product(name='Octobre', price=20.0, sy=sy)
#         self.novembre   = _create_product(name='Novembre', price=20.0, sy=sy)

#         # Products - ALSH
#         self.tous1 = _create_product(name='Toussaint 1', sy=sy, date='2019-10-10',
#                                      category=14, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
#         self.tous2 = _create_product(name='Toussaint 2', sy=sy, date='2019-10-11',
#                                      category=14, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
#         self.tous3 = _create_product(name='Toussaint 3', sy=sy, date='2019-10-12',
#                                      category=14, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
#         self.tous4 = _create_product(name='Toussaint 4', sy=sy, date='2019-10-13',
#                                      category=14, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
#         self.tous5 = _create_product(name='Toussaint 5', sy=sy, date='2019-10-14',
#                                      category=14, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)

#         self.noel1 = _create_product(name='Noel 1', sy=sy, date='2019-12-10',
#                                      category=15, subcategory=2, price=20.0, price_q2=7.0, price_q1=2.0)
#         self.noel2 = _create_product(name='Noel 2', sy=sy, date='2019-12-11',
#                                      category=15, subcategory=2, price=20.0, price_q2=7.0, price_q1=2.0)
#         self.noel3 = _create_product(name='Noel 3', sy=sy, date='2019-12-12',
#                                      category=15, subcategory=2, price=20.0, price_q2=7.0, price_q1=2.0)
#         self.noel4 = _create_product(name='Noel 4', sy=sy, date='2019-12-13',
#                                      category=15, subcategory=2, price=20.0, price_q2=7.0, price_q1=2.0)
#         self.noel5 = _create_product(name='Noel 5', sy=sy, date='2019-12-14',
#                                      category=15, subcategory=2, price=20.0, price_q2=7.0, price_q1=2.0)

#         self.aout1 = _create_product(name='Aout 1', sy=sy, date='2020-08-10',
#                                      category=19, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
#         self.aout2 = _create_product(name='Aout 2', sy=sy, date='2020-08-11',
#                                      category=19, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
#         self.aout3 = _create_product(name='Aout 3', sy=sy, date='2020-08-12',
#                                      category=19, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
#         self.aout4 = _create_product(name='Aout 4', sy=sy, date='2020-08-13',
#                                      category=19, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
#         self.aout5 = _create_product(name='Aout 5', sy=sy, date='2020-08-14',
#                                      category=19, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)

#         # Order
#         self.order = Order.objects.create(
#             payer=self.p1.id,
#             caster=self.p1.id 
#         )

#     def test_keys_errors(self):
#         r = OrderHelper.verify({})
#         self.assertEqual(r['status'], 'Failure')
#         self.assertIn('KeyError', r['message'])

#         # r = OrderHelper.verify({
#         #     'payer': self.p1.id,
#         #     'caster': self.p1.id,
#         #     'peri': [
#         #         {
#         #             'product': 0
#         #         }
#         #     ],
#         #     'alsh': [],
#         # })
#         # self.assertEqual(r['status'], 'Failure')
#         # self.assertIn('KeyError', r['message'])

#         # r = OrderHelper.verify({
#         #     'payer': self.p1.id,
#         #     'caster': self.p1.id,
#         #     'peri': [],
#         #     'alsh': [
#         #         {
#         #             'child': 0
#         #         }
#         #     ],
#         # })
#         # self.assertEqual(r['status'], 'Failure')
#         # self.assertIn('KeyError', r['message'])

#     """ Will failed cuz I commented payer and caster verifications """
#     """
#     def test_invalid_parent_and_caster(self):
#         r = OrderHelper.verify({
#             'payer': 0,
#             'caster': 0,
#             'peri': [],
#             'alsh': []
#         })
#         self.assertEqual(r['status'], 'Failure')
#         self.assertIn('Payer does not exist with ID', r['message'])

#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': 0,
#             'peri': [],
#             'alsh': []
#         })
#         self.assertEqual(r['status'], 'Failure')
#         self.assertIn('Caster does not exist with ID', r['message'])
#     """

#     def test_sibling_does_not_exist(self):
#         r = OrderHelper.verify({
#             'payer': self.p2.id,
#             'caster': self.p2.id,
#             'peri': [],
#             'alsh': []
#         })
#         self.assertEqual(r['status'], 'Failure')
#         self.assertEqual('Sibling does not exist for payer.', r['message'])

#     """ NOTE: nothing happens when there is no child """
#     def test_peri_no_children(self):
#         pass
#         # r = OrderHelper.verify({
#         #     'payer': self.p1.id,
#         #     'caster': self.p1.id,
#         #     'peri': [{'product': 0, 'children': []}],
#         #     'alsh': []
#         # })
#         # self.assertEqual(r['status'], 'Failure')
#         # self.assertEqual('Sibling does not exist for payer.', r['message'])

#     """ Ensure product ID is correct """
#     def test_peri_product_does_not_exist(self):
#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [{'product': 0, 'children': [self.c1.id]}],
#             'alsh': []
#         })
#         obs = r['tickets_invalid'][0]['obs']
#         self.assertEqual(r['status'], 'Failure')

#         self.assertEqual('Product not found.', obs)

#     """ Ensure child is bound to parent """
#     def test_peri_child_not_in_sibling(self):
#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [{'product': self.septembre.id, 'children': [self.c10.id]}],
#             'alsh': []
#         })
#         obs = r['tickets_invalid'][0]['obs']
#         self.assertEqual(r['status'], 'Failure')
#         self.assertEqual('Child is not bind to parent.', obs)

#     """ Ensure child can't have the same product """
#     def test_peri_product_already_bought(self):
#         _create_ticket(
#             self.c1.id,
#             self.septembre.id,
#             self.septembre.price,
#             self.order
#         )
        
#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [{
#                 'product': self.septembre.id, 
#                 'children': [self.c1.id]
#             }],
#             'alsh': []
#         })
#         obs = r['tickets_invalid'][0]['obs']
#         self.assertEqual(r['status'], 'Failure')
#         self.assertEqual('Product already bought.', obs)

#     """ Ensure amount is correct for one child """
#     def test_peri_correct_amount(self):
#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [
#                 {
#                     'product': self.septembre.id,
#                     'children': [self.c1.id]
#                 },
#                 {
#                     'product': self.octobre.id,
#                     'children': [self.c2.id]
#                 },
#                 {
#                     'product': self.novembre.id,
#                     'children': [self.c3.id]
#                 }
#             ],
#             'alsh': []
#         })
#         self.assertEqual(r['status'], 'Success')
#         self.assertEqual(60.0, r['amount'])

#     """ Ensure amount is correct for multiple children """
#     def test_peri_correct_amount_multiple_children(self):
#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [
#                 {
#                     'product': self.septembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id,
#                         self.c4.id,
#                         self.c5.id
#                     ]
#                 },
#                 {
#                     'product': self.octobre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id
#                     ]
#                 },
#                 {
#                     'product': self.novembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id
#                     ]
#                 }
#             ],
#             'alsh': []
#         })
#         self.assertEqual(r['status'], 'Success')
#         self.assertEqual(132.0, r['amount'])

#     """ Ensure child is bound to parent """
#     def test_alsh_child_not_in_sibling(self):
#         # print('test_alsh_child_not_in_sibling')

#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [],
#             'alsh': [{
#                 'child': self.c10.id,
#                 'products': [0]
#             }]
#         })
#         # print (r)

#         obs = r['tickets_invalid'][0]['obs']
#         self.assertEqual(r['status'], 'Failure')
#         self.assertEqual('Child is not bind to parent.', obs)

#     """ Ensure child ID is valid """
#     def test_alsh_invalid_child(self):
#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [],
#             'alsh': [{
#                 'child': 100000,
#                 'products': [0]
#             }]
#         })
#         obs = r['tickets_invalid'][0]['obs']
#         self.assertEqual(r['status'], 'Failure')
#         self.assertEqual('Child does not exist.', obs)

#     """ Ensure classroom is correct """
#     def test_alsh_classroom_not_set(self):
#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [],
#             'alsh': [{
#                 'child': self.c5.id,
#                 'products': [0]
#             }]
#         })
#         obs = r['tickets_invalid'][0]['obs']
#         self.assertEqual(r['status'], 'Failure')
#         self.assertEqual('Classroom not set.', obs)

#     """ """
#     def test_alsh_product_does_not_exist(self):
#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [],
#             'alsh': [{
#                 'child': self.c4.id,
#                 'products': [0]
#             }]
#         })
#         obs = r['tickets_invalid'][0]['obs']
#         self.assertEqual(r['status'], 'Failure')
#         self.assertEqual('Product not found.', obs)

#     """ """
#     def test_alsh_product_out_of_stock(self):
#         # print ('test_alsh_product_out_of_stock')

#         # Prepare stock
#         _alter_stock(
#             self.tous1,
#             _max=1,
#             count=1
#         )

#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [],
#             'alsh': [{
#                 'child': self.c4.id,
#                 'products': [self.tous1.id]
#             }]
#         })
#         obs = r['tickets_invalid'][0]['obs']
#         self.assertEqual(r['status'], 'Failure')
#         self.assertEqual('Product out of stock.', obs)
    
#     """ """
#     def test_alsh_invalid_subcategory(self):
#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [],
#             'alsh': [{
#                 'child': self.c4.id,
#                 'products': [self.tous1.id]
#             }]
#         })
#         obs = r['tickets_invalid'][0]['obs']
#         self.assertEqual(r['status'], 'Failure')
#         self.assertEqual('Wrong product for the age.', obs)

#     """ Ensure child can't buy the same product (if less than 3yo) """
#     def test_alsh_l3_product_already_bought(self):
#         _create_ticket(
#             self.c1.id,
#             self.tous1.id,
#             0.0,
#             self.order
#         )

#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [],
#             'alsh': [{
#                 'child': self.c1.id,
#                 'products': [self.tous1.id]
#             }]
#         })

#         obs = r['tickets_invalid'][0]['obs']
#         self.assertEqual(r['status'], 'Failure')
#         self.assertEqual('Product already bought.', obs)

#     """ Ensure amount is correct (if less than 3yo) """
#     def test_alsh_l3_correct_amount(self):
#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [],
#             'alsh': [{
#                 'child': self.c1.id,
#                 'products': [self.tous1.id]
#             }]
#         })

#         self.assertEqual(r['status'], 'Success')
#         self.assertEqual(17.0, r['amount'])

#     """ """
#     def test_alsh_p3_product_already_bought(self):
#         _create_ticket(
#             self.c3.id,
#             self.noel1.id,
#             0.0,
#             self.order
#         )

#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [],
#             'alsh': [{
#                 'child': self.c3.id,
#                 'products': [self.noel1.id]
#             }]
#         })

#         obs = r['tickets_invalid'][0]['obs']
#         self.assertEqual(r['status'], 'Failure')
#         self.assertEqual('Product already bought.', obs)

#     """ Ensure amount is correct if there is less than 5 products """
#     def test_alsh_p3_correct_amount_less_than_5(self):
#         _create_ticket(
#             self.c3.id,
#             self.noel1.id,
#             0.0,
#             self.order
#         )
#         _create_ticket(
#             self.c3.id,
#             self.noel2.id,
#             0.0,
#             self.order
#         )

#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [],
#             'alsh': [{
#                 'child': self.c3.id,
#                 'products': [self.noel2.id, self.noel3.id, self.noel4.id]
#             }]
#         })

#         self.assertEqual(r['status'], 'Success')
#         self.assertEqual(40.0, r['amount'])

#     """ """
#     def test_alsh_p3_correct_amount_and_quotient(self):
#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [],
#             'alsh': [
#                 {
#                     # MINUS 6
#                     'child': self.c2.id,
#                     'products': [
#                         # Q2
#                         self.tous1.id,
#                         self.tous2.id,
#                         self.tous3.id, 
#                         self.tous4.id,
#                         self.tous5.id,
#                         # Q1
#                         self.aout1.id,
#                         self.aout2.id,
#                         self.aout3.id,
#                         self.aout4.id,
#                         self.aout5.id,
#                     ],
#                 },
#                 {
#                     'child': self.c3.id,
#                     'products': [
#                         # Q1
#                         self.noel1.id,
#                         self.noel2.id,
#                         self.noel3.id,
#                         self.noel4.id,
#                         self.noel5.id
#                     ],
#                 },
#                 {
#                     'child': self.c4.id,
#                     'products': [
#                         # NE
#                         self.noel1.id,
#                         self.noel2.id,
#                         self.noel3.id,
#                         self.noel4.id,
#                         self.noel5.id
#                     ],
#                 },
#             ]
#         })

#         self.assertEqual(r['status'], 'Success')
#         self.assertEqual(130.0, r['amount'])

#     """ Ensure the amount is correct if child get 3yo at the date of the product """
#     def test_alsh_l3_date(self):
#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             'peri': [],
#             'alsh': [{
#                 'child': self.c1.id,
#                 'products': [
#                     self.aout1.id,
#                     self.aout2.id,
#                     self.aout3.id,
#                     self.aout4.id,
#                     self.aout5.id
#                 ]
#             }]
#         })

#         self.assertEqual(r['status'], 'Success')
#         self.assertEqual(20.0, r['amount'])

#     """ """
#     def test_final_correct_amount(self):
#         r = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             # 132 €
#             'peri': [
#                 {
#                     'product': self.septembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id,
#                         self.c4.id,
#                         self.c5.id
#                     ]
#                 },
#                 {
#                     'product': self.octobre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id
#                     ]
#                 },
#                 {
#                     'product': self.novembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id
#                     ]
#                 }
#             ],
#             'alsh': []
#         })
#         self.assertEqual(r['status'], 'Success')
#         self.assertEqual(132.0, r['amount'])


# """ """
# class OrderHelperTest(BaseViewTest):
    
#     def setUp(self):
#         """ Macros """
#         def macro_create_child(dob, q1, q2, cl):
#             tmp = _create_user(
#                 '', '', dob,
#                 {
#                     'q1': q1,
#                     'q2': q2,
#                     'classroom': cl
#                 }
#             )
#             return tmp['user'], tmp['record']

#         """ Main """

#         # Parent 1
#         self.p1 = _create_user('', '', None)['user']

#         # Child 1 - Bind
#         self.c1, self.r1 = macro_create_child('2017-06-01', 1, 2, 1)

#         # Child 2 - Bind
#         self.c2, self.r2 = macro_create_child('2015-03-01', 2, 3, 1)

#         # Child 3 - Bind
#         self.c3, self.r3 = macro_create_child('2014-03-01', 3, 1, 5)

#         # Child 4 - Bind
#         self.c4, self.r4 = macro_create_child('2013-03-01', 1, 3, 6)

#         # Child 5 - Bind
#         # Classroom set to 0 for test_alsh_classroom_not_set
#         self.c5, self.r5 = macro_create_child('2012-03-01', 2, 1, 0)

#         # Sibling
#         Child.objects.create(id=100000, user=100000)
#         # print ('USER: {}'.format(Child.objects.get(id=100000).user))
#         self.sibling = _create_sibling(
#             self.p1.id,
#             [
#                 self.c1.id,
#                 self.c2.id,
#                 self.c3.id,
#                 self.c4.id,
#                 self.c5.id,
#                 100000  # Fake ID - ALSH bound but don't exist
#             ]
#         )

#         # Parent 2 - No bound children
#         self.p2 = _create_user('', '', None)['user']

#         # Child 10 - No sibling
#         self.c10, self.r10 = macro_create_child(None, 0, 0, 0)

#         # Products
#         sy = SchoolYear.objects.create(
#             date_start='2019-09-01', date_end='2020-08-30')

#         # Products - PERI
#         self.septembre = _create_product(name='Septembre', price=20.0, sy=sy)
#         self.octobre = _create_product(name='Octobre', price=20.0, sy=sy)
#         self.novembre = _create_product(name='Novembre', price=20.0, sy=sy)

#         # Products - ALSH
#         self.tous1 = _create_product(name='Toussaint 1', sy=sy, date='2019-10-10',
#                                      category=14, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
#         self.tous2 = _create_product(name='Toussaint 2', sy=sy, date='2019-10-11',
#                                      category=14, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
#         self.tous3 = _create_product(name='Toussaint 3', sy=sy, date='2019-10-12',
#                                      category=14, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
#         self.tous4 = _create_product(name='Toussaint 4', sy=sy, date='2019-10-13',
#                                      category=14, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
#         self.tous5 = _create_product(name='Toussaint 5', sy=sy, date='2019-10-14',
#                                      category=14, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)

#         self.noel1 = _create_product(name='Noel 1', sy=sy, date='2019-12-10',
#                                      category=15, subcategory=2, price=20.0, price_q2=7.0, price_q1=2.0)
#         self.noel2 = _create_product(name='Noel 2', sy=sy, date='2019-12-11',
#                                      category=15, subcategory=2, price=20.0, price_q2=7.0, price_q1=2.0)
#         self.noel3 = _create_product(name='Noel 3', sy=sy, date='2019-12-12',
#                                      category=15, subcategory=2, price=20.0, price_q2=7.0, price_q1=2.0)
#         self.noel4 = _create_product(name='Noel 4', sy=sy, date='2019-12-13',
#                                      category=15, subcategory=2, price=20.0, price_q2=7.0, price_q1=2.0)
#         self.noel5 = _create_product(name='Noel 5', sy=sy, date='2019-12-14',
#                                      category=15, subcategory=2, price=20.0, price_q2=7.0, price_q1=2.0)

#         self.aout1 = _create_product(name='Aout 1', sy=sy, date='2020-08-10',
#                                      category=19, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
#         self.aout2 = _create_product(name='Aout 2', sy=sy, date='2020-08-11',
#                                      category=19, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
#         self.aout3 = _create_product(name='Aout 3', sy=sy, date='2020-08-12',
#                                      category=19, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
#         self.aout4 = _create_product(name='Aout 4', sy=sy, date='2020-08-13',
#                                      category=19, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)
#         self.aout5 = _create_product(name='Aout 5', sy=sy, date='2020-08-14',
#                                      category=19, subcategory=1, price=17.0, price_q2=4.0, price_q1=0.0)

#         # Order
#         self.order = Order.objects.create(
#             name='Initial order',
#             payer=self.p1.id,
#             caster=self.p1.id
#         )
#         self.order.status.create(status=StatusEnum.COMPLETED)
#         self.order.methods.create()
#         self.order.tickets.create()
#         self.order.tickets.last().status.create(status=StatusEnum.COMPLETED)

#     """
#     OLD: Base tests for OrderStock model and logic 
#     NEW: Base tests for ProductStock model and logic 
#     """
#     def test_stock_product_does_not_exist(self):
#         r = ParamsHelper.Stock.has_stock(1000)
#         self.assertFalse(r)

#     def test_stock_model_does_not_exist(self):
#         r = ParamsHelper.Stock.has_stock(self.tous1.id)
#         self.assertTrue(r)

#     def test_stock_unlimited_stock(self):
#         r = ParamsHelper.Stock.has_stock(self.tous1.id)
#         self.assertTrue(r)

#     def test_stock_out_of_stock(self):
#         _alter_stock(
#             self.tous1,
#             _max=1,
#             count=1
#         )

#         r = ParamsHelper.Stock.has_stock(self.tous1.id)
#         self.assertFalse(r)

#     def test_stock_has_stock(self):
#         _alter_stock(
#             self.tous1,
#             _max=2,
#             count=1
#         )
#         r = ParamsHelper.Stock.has_stock(self.tous1.id)
#         self.assertTrue(r)
    
#     def test_stock_increase(self):
#         s = _alter_stock(
#             self.tous1,
#             _max=10,
#             count=1
#         )

#         r = ParamsHelper.Stock.inc(self.tous1.id)
        
#         order_stock = ProductStock.objects.get(pk=s.id)

#         self.assertEqual(s.id, order_stock.id)
#         self.assertEqual(order_stock.count, 2)

#     def test_stock_decrease(self):
#         print ('test_stock_decrease')

#         s = _alter_stock(
#             self.tous1,
#             _max=10,
#             count=1
#         )
#         r = ParamsHelper.Stock.dec(self.tous1.id)
#         print (r)

#         order_stock = ProductStock.objects.get(pk=s.id)
#         self.assertEqual(order_stock.count, 0)
    

#     """
#     Tests for reports
#     """
#     def test_report_invalid_sibling(self):
#         # t1 = Ticket.objects.create(order=self.order, payee = self.c1.id, price=20.0)
#         # t2 = Ticket.objects.create(order=self.order, payee = self.c2.id, price=20.0)
#         # t3 = Ticket.objects.create(order=self.order, payee = 10000, price=20.0)
        
#         r = OrderHelper.report({
#             'client': self.p2.id,
#             'tickets': [
#                 # t1.id,
#                 # t2.id,
#                 # t3.id
#             ]
#         })
#         # print (r)
#         self.assertIn(r, 'Failed to get sibling for parent: {}.'.format(self.p2.id))

#     def test_report(self):
#         # print ('test_report')
#         t1 = Ticket.objects.create(order=self.order, payee=self.c1.id, price=20.0)
#         t2 = Ticket.objects.create(order=self.order, payee=self.c2.id, price=20.0)
#         t3 = Ticket.objects.create(order=self.order, payee=10000, price=20.0)
        
#         r = OrderHelper.report({
#             'client': self.p1.id,
#             'tickets': [
#                 t1.id,
#                 # t2.id,
#                 # t3.id
#             ]
#         })
#         self.assertEqual(r.credit.amount, 20.0)

#         r = OrderHelper.report({
#             'client': self.p1.id,
#             'tickets': [
#                 # t1.id,
#                 t2.id,
#                 # t3.id
#             ]
#         })
#         self.assertEqual(r.credit.amount, 40.0)

#         r = OrderHelper.report({
#             'client': self.p1.id,
#             'tickets': [
#                 t3.id
#             ]
#         })

#         self.assertEqual(r.credit.amount, 40.0)

#         # Tickets
#         t1 = Ticket.objects.get(pk=t1.id)
#         status = t1.status.last()

#         self.assertEqual(status.status, StatusEnum.REPORTED)

#     """ """
#     def test_create_order(self):
#         # print ('test_create_order')

#         v = OrderHelper.verify({
#             'payer': self.p1.id,
#             'caster': self.p1.id,
#             # 132 €
#             'peri': [
#                 {
#                     'product': self.septembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id,
#                         self.c4.id,
#                         self.c5.id
#                     ]
#                 },
#                 {
#                     'product': self.octobre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id
#                     ]
#                 },
#                 {
#                     'product': self.novembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id
#                     ]
#                 }
#             ],
#             'alsh': [
#                 {
#                     # MINUS 6
#                     'child': self.c2.id,
#                     'products': [
#                         # Q2
#                         self.tous1.id,
#                         self.tous2.id,
#                         self.tous3.id,
#                         self.tous4.id,
#                         self.tous5.id,
#                         # Q1
#                         self.aout1.id,
#                         self.aout2.id,
#                         self.aout3.id,
#                         self.aout4.id,
#                         self.aout5.id,
#                     ],
#                 },
#                 {
#                     'child': self.c3.id,
#                     'products': [
#                         # Q1
#                         self.noel1.id,
#                         self.noel2.id,
#                         self.noel3.id,
#                         self.noel4.id,
#                         self.noel5.id
#                     ],
#                 },
#                 {
#                     'child': self.c4.id,
#                     'products': [
#                         # NE
#                         self.noel1.id,
#                         self.noel2.id,
#                         self.noel3.id,
#                         self.noel4.id,
#                         self.noel5.id
#                     ],
#                 },
#             ]
#         })

#         # print (v)

#         self.assertEqual(v['status'], 'Success')
#         self.assertEqual(262.0, v['amount'])

#         r = OrderHelper._create({
#             'name': 'Test Payment',
#             'comment': '...',

#             'reference': '007',
#             'type': OrderTypeEnum.OFFICE,

#             'payer': self.p1.id,
#             'caster': self.p1.id,

#             'status': {
#                 'status': StatusEnum.COMPLETED
#             },

#             'methods': [
#                 {
#                     'amount': 130.0,
#                     'method': MethodEnum.CASH,
#                     'reference': ''
#                 },
#                 {
#                     'amount': 132.0,
#                     'method': MethodEnum.CHECK,
#                     'reference': '000007'
#                 }
#             ],

#             'amount': v['amount'],
#             'tickets': v['tickets']
#         })

#         # print (r)

#         order = Order.objects.last()
#         status = order.status.last()
#         tickets = order.tickets.all()
#         methods = order.methods.all()
#         tstatus = tickets[0].status.last()

#         # print (f'r.id = {r.id} x order.id = {order.id}')

#         self.assertEqual(order.name, 'Test Payment')
#         self.assertEqual(order.type, OrderTypeEnum.OFFICE)
#         self.assertEqual(order.reference, '007')

#         self.assertEqual(status.status, StatusEnum.COMPLETED)

#         self.assertEqual(methods[0].amount, 130.0)
#         self.assertEqual(methods[1].amount, 132.0)

#         self.assertEqual(len(tickets), 30)
#         self.assertEqual(tstatus.status, StatusEnum.COMPLETED)


#     """
#     Tests for payment
#     """

#     """ """
#     def test_pay_order_verify_failed(self):
#         r = OrderHelper.pay({
#             'name': 'Test Payment',
#             'comment': '...',

#             'reference': '007',
#             'type': OrderTypeEnum.OFFICE,

#             'payer': 0,
#             'caster': self.p1.id,

#             'methods': [
#                 {
#                     'amount': 130.0,
#                     'method': MethodEnum.CASH,
#                     'reference': ''
#                 },
#                 {
#                     'amount': 132.0,
#                     'method': MethodEnum.CHECK,
#                     'reference': '000007'
#                 }
#             ],

#             'amount': 262.0,

#             # 262 €
#             'peri': [
#                 {
#                     'product': self.septembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id,
#                         self.c4.id,
#                         self.c5.id
#                     ]
#                 },
#                 {
#                     'product': self.octobre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id
#                     ]
#                 },
#                 {
#                     'product': self.novembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id
#                     ]
#                 }
#             ],
#             'alsh': [
#                 {
#                     # MINUS 6
#                     'child': self.c2.id,
#                     'products': [
#                         # Q2
#                         self.tous1.id,
#                         self.tous2.id,
#                         self.tous3.id,
#                         self.tous4.id,
#                         self.tous5.id,
#                         # Q1
#                         self.aout1.id,
#                         self.aout2.id,
#                         self.aout3.id,
#                         self.aout4.id,
#                         self.aout5.id,
#                     ],
#                 },
#                 {
#                     'child': self.c3.id,
#                     'products': [
#                         # Q1
#                         self.noel1.id,
#                         self.noel2.id,
#                         self.noel3.id,
#                         self.noel4.id,
#                         self.noel5.id
#                     ],
#                 },
#                 {
#                     'child': self.c4.id,
#                     'products': [
#                         # NE
#                         self.noel1.id,
#                         self.noel2.id,
#                         self.noel3.id,
#                         self.noel4.id,
#                         self.noel5.id
#                     ],
#                 },
#             ]
#         })

#         self.assertEqual(r['status'], 'Failure')
#         self.assertEqual(r['message'], 'Sibling does not exist for payer.')

#     """ """
#     def test_pay_order_invalid_products(self):
#         # print('test_pay_order_invalid_products')

#         r = OrderHelper.pay({
#             'name': 'Test Payment',
#             'comment': '...',

#             'reference': '007',
#             'type': OrderTypeEnum.OFFICE,

#             'payer': self.p1.id,
#             'caster': self.p1.id,

#             'methods': [
#                 {
#                     'amount': 130.0,
#                     'method': MethodEnum.CASH,
#                     'reference': ''
#                 },
#                 {
#                     'amount': 132.0,
#                     'method': MethodEnum.CHECK,
#                     'reference': '000007'
#                 }
#             ],

#             'amount': 262.0,

#             # 262 €
#             'peri': [
#                 {
#                     'product': self.septembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id,
#                         self.c4.id,
#                         self.c5.id,
#                         self.c10.id
#                     ]
#                 },
#                 {
#                     'product': self.octobre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id
#                     ]
#                 },
#                 {
#                     'product': self.novembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id
#                     ]
#                 }
#             ],
#             'alsh': [
#                 {
#                     # MINUS 6
#                     'child': self.c2.id,
#                     'products': [
#                         # Q2
#                         self.tous1.id,
#                         self.tous2.id,
#                         self.tous3.id,
#                         self.tous4.id,
#                         self.tous5.id,
#                         # Q1
#                         self.aout1.id,
#                         self.aout2.id,
#                         self.aout3.id,
#                         self.aout4.id,
#                         self.aout5.id,
#                     ],
#                 },
#                 {
#                     'child': self.c3.id,
#                     'products': [
#                         # Q1
#                         self.noel1.id,
#                         self.noel2.id,
#                         self.noel3.id,
#                         self.noel4.id,
#                         self.noel5.id
#                     ],
#                 },
#                 {
#                     'child': self.c4.id,
#                     'products': [
#                         # NE
#                         self.noel1.id,
#                         self.noel2.id,
#                         self.noel3.id,
#                         self.noel4.id,
#                         self.noel5.id
#                     ],
#                 },
#             ]
#         })

#         # print(f'c10 ID: {self.c10.id}')
#         # print (r)

#         self.assertEqual(r['status'], 'Failure')
#         self.assertEqual(r['message'], 'Cart contains invalid products.')

#     """ """
#     def test_pay_order_incorrect_amount(self):
#         # print('test_pay_order_incorrect_amount')

#         r = OrderHelper.pay({
#             'name': 'Test Payment',
#             'comment': '...',

#             'reference': '007',
#             'type': OrderTypeEnum.OFFICE,

#             'payer': self.p1.id,
#             'caster': self.p1.id,

#             'methods': [
#                 {
#                     'amount': 130.0,
#                     'method': MethodEnum.CASH,
#                     'reference': ''
#                 },
#                 {
#                     'amount': 131.0,
#                     'method': MethodEnum.CHECK,
#                     'reference': '000007'
#                 }
#             ],

#             # 262 €
#             'peri': [
#                 {
#                     'product': self.septembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id,
#                         self.c4.id,
#                         self.c5.id,
#                     ]
#                 },
#                 {
#                     'product': self.octobre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id
#                     ]
#                 },
#                 {
#                     'product': self.novembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id
#                     ]
#                 }
#             ],
#             'alsh': [
#                 {
#                     # MINUS 6
#                     'child': self.c2.id,
#                     'products': [
#                         # Q2
#                         self.tous1.id,
#                         self.tous2.id,
#                         self.tous3.id,
#                         self.tous4.id,
#                         self.tous5.id,
#                         # Q1
#                         self.aout1.id,
#                         self.aout2.id,
#                         self.aout3.id,
#                         self.aout4.id,
#                         self.aout5.id,
#                     ],
#                 },
#                 {
#                     'child': self.c3.id,
#                     'products': [
#                         # Q1
#                         self.noel1.id,
#                         self.noel2.id,
#                         self.noel3.id,
#                         self.noel4.id,
#                         self.noel5.id
#                     ],
#                 },
#                 {
#                     'child': self.c4.id,
#                     'products': [
#                         # NE
#                         self.noel1.id,
#                         self.noel2.id,
#                         self.noel3.id,
#                         self.noel4.id,
#                         self.noel5.id
#                     ],
#                 },
#             ]
#         })

#         # print (f'c10 ID: {self.c10.id}')
#         # print (r)

#         self.assertEqual(r['status'], 'Failure')
#         self.assertIn('Incorrect amount.', r['message'])

#     """ """
#     def test_pay_order_order_creation_failed(self):
#         r = OrderHelper.pay({
#             'name': 'Test Payment',
#             'comment': '...',

#             'reference': '007',
#             'type': OrderTypeEnum.OFFICE,

#             'payer': self.p1.id,
#             'caster': self.p1.id,

#             'methods': [
#                 {
#                     'amount': 130.0,
#                     'method': MethodEnum.CASH,
#                     'reference': ''
#                 },
#                 {
#                     'amount': 132.0,
#                     'method': MethodEnum.CHECK,
#                     'reference': '000007'
#                 }
#             ],

#             'amount': 262.0,

#             # 262 €
#             'peri': [
#                 {
#                     'product': self.septembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id,
#                         self.c4.id,
#                         self.c5.id
#                     ]
#                 },
#                 {
#                     'product': self.octobre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id
#                     ]
#                 },
#                 {
#                     'product': self.novembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id
#                     ]
#                 }
#             ],
#             'alsh': [
#                 {
#                     # MINUS 6
#                     'child': self.c2.id,
#                     'products': [
#                         # Q2
#                         self.tous1.id,
#                         self.tous2.id,
#                         self.tous3.id,
#                         self.tous4.id,
#                         self.tous5.id,
#                         # Q1
#                         self.aout1.id,
#                         self.aout2.id,
#                         self.aout3.id,
#                         self.aout4.id,
#                         self.aout5.id,
#                     ],
#                 },
#                 {
#                     'child': self.c3.id,
#                     'products': [
#                         # Q1
#                         self.noel1.id,
#                         self.noel2.id,
#                         self.noel3.id,
#                         self.noel4.id,
#                         self.noel5.id
#                     ],
#                 },
#                 {
#                     'child': self.c4.id,
#                     'products': [
#                         # NE
#                         self.noel1.id,
#                         self.noel2.id,
#                         self.noel3.id,
#                         self.noel4.id,
#                         self.noel5.id
#                     ],
#                 },
#             ]
#         })

#         # self.assertEqual(v['status'], 'Success')
#         # self.assertEqual(262.0, v['amount'])
    
#     """ """
#     def test_pay_order(self):
#         r = OrderHelper.pay({
#             'name': 'Test Payment',
#             'comment': '...',

#             'reference': '007',
#             'type': OrderTypeEnum.OFFICE,

#             'payer': self.p1.id,
#             'caster': self.p1.id,

#             'methods': [
#                 {
#                     'amount': 130.0,
#                     'method': MethodEnum.CASH,
#                     'reference': ''
#                 },
#                 {
#                     'amount': 132.0,
#                     'method': MethodEnum.CHECK,
#                     'reference': '000007'
#                 }
#             ],

#             # 262 €
#             'peri': [
#                 {
#                     'product': self.septembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id,
#                         self.c4.id,
#                         self.c5.id,
#                     ]
#                 },
#                 {
#                     'product': self.octobre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id
#                     ]
#                 },
#                 {
#                     'product': self.novembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id
#                     ]
#                 }
#             ],
#             'alsh': [
#                 {
#                     # MINUS 6
#                     'child': self.c2.id,
#                     'products': [
#                         # Q2
#                         self.tous1.id,
#                         self.tous2.id,
#                         self.tous3.id,
#                         self.tous4.id,
#                         self.tous5.id,
#                         # Q1
#                         self.aout1.id,
#                         self.aout2.id,
#                         self.aout3.id,
#                         self.aout4.id,
#                         self.aout5.id,
#                     ],
#                 },
#                 {
#                     'child': self.c3.id,
#                     'products': [
#                         # Q1
#                         self.noel1.id,
#                         self.noel2.id,
#                         self.noel3.id,
#                         self.noel4.id,
#                         self.noel5.id
#                     ],
#                 },
#                 {
#                     'child': self.c4.id,
#                     'products': [
#                         # NE
#                         self.noel1.id,
#                         self.noel2.id,
#                         self.noel3.id,
#                         self.noel4.id,
#                         self.noel5.id
#                     ],
#                 },
#             ]
#         })

#         self.assertEqual(r['status'], 'Success')
#         self.assertTrue(r['order']['id'])

#         order = Order.objects.get(pk=r['order']['id'])
#         status = order.status.filter(status=StatusEnum.COMPLETED)

#         self.assertTrue(status)

#     """
#     Tests for payment with reports
#     """

#     """ Ensure the credit is consumed and updated if credit is greater """
#     def test_pay_report_credit_greater(self):
#         t1 = Ticket.objects.create(order=self.order, payee=self.c1.id, price=20.0)
#         t2 = Ticket.objects.create(order=self.order, payee=self.c2.id, price=20.0)
        
#         c = OrderHelper.report({
#             'client': self.p1.id,
#             'tickets': [
#                 t1.id,
#                 t2.id,
#             ]
#         })
#         self.assertEqual(c.credit.amount, 40.0)
        
#         r = OrderHelper.pay({
#             'name': 'Test Payment',
#             'comment': '...',

#             'reference': '007',
#             'type': OrderTypeEnum.OFFICE,

#             'payer': self.p1.id,
#             'caster': self.p1.id,
            
#             'methods': [],

#             # 20 €
#             'peri': [
#                 {
#                     'product': self.septembre.id,
#                     'children': [
#                         self.c1.id
#                     ]
#                 }
#             ],
#             'alsh': []
#         })

#         self.assertEqual(r['status'], 'Success')
#         self.assertTrue(r['order']['id'])

#         order = Order.objects.get(pk=r['order']['id'])
#         status = order.status.filter(status=StatusEnum.COMPLETED)

#         self.assertTrue(status)

#         # Credit
#         credit = ClientCredit.objects.get(pk=c.credit.id)
#         self.assertEqual(credit.amount, 20.0)

#     """ Ensure the credit is consumed and updated if credit is lesser """
#     def test_pay_report_credit_lesser(self):
#         t1 = Ticket.objects.create(order=self.order, payee=self.c1.id, price=20.0)
        
#         c = OrderHelper.report({
#             'client': self.p1.id,
#             'tickets': [
#                 t1.id,
#             ]
#         })
#         self.assertEqual(c.credit.amount, 20.0)
        
#         r = OrderHelper.pay({
#             'name': 'Test Payment',
#             'comment': '...',

#             'reference': '007',
#             'type': OrderTypeEnum.OFFICE,

#             'payer': self.p1.id,
#             'caster': self.p1.id,
            
#             'methods': [{
#                 'method': MethodEnum.CASH,
#                 'amount': 20.0,
#                 'reference': ''
#             }],

#             # 40 €
#             'peri': [
#                 {
#                     'product': self.septembre.id,
#                     'children': [
#                         self.c1.id,
#                     ]
#                 },
#                 {
#                     'product': self.octobre.id,
#                     'children': [
#                         self.c1.id,
#                     ]
#                 }
#             ],
#             'alsh': []
#         })

#         self.assertEqual(r['status'], 'Success')
#         self.assertTrue(r['order']['id'])

#         order = Order.objects.get(pk=r['order']['id'])
#         status = order.status.filter(status=StatusEnum.COMPLETED)

#         self.assertTrue(status)

#         # Credit
#         credit = ClientCredit.objects.get(pk=c.credit.id)
#         self.assertEqual(credit.amount, 0.0)

#     """ Ensure the credit is consumed and updated if credit is equal """
#     def test_pay_report_credit_equal(self):
#         # print ('test_pay_report_credit_equal')
#         t1 = Ticket.objects.create(order=self.order, payee=self.c1.id, price=20.0)
#         t2 = Ticket.objects.create(order=self.order, payee=self.c2.id, price=20.0)
        
#         c = OrderHelper.report({
#             'client': self.p1.id,
#             'tickets': [
#                 t1.id,
#                 t2.id
#             ]
#         })
#         self.assertEqual(c.credit.amount, 40.0)
        
#         r = OrderHelper.pay({
#             'name': 'Test Payment',
#             'comment': '...',

#             'reference': '007',
#             'type': OrderTypeEnum.OFFICE,

#             'payer': self.p1.id,
#             'caster': self.p1.id,
            
#             'methods': [],

#             # 40 €
#             'peri': [
#                 {
#                     'product': self.septembre.id,
#                     'children': [
#                         self.c1.id,
#                     ]
#                 },
#                 {
#                     'product': self.octobre.id,
#                     'children': [
#                         self.c1.id,
#                     ]
#                 }
#             ],
#             'alsh': []
#         })

#         # print (r)

#         self.assertEqual(r['status'], 'Success')
#         self.assertTrue(r['order']['id'])

#         order = Order.objects.get(pk=r['order']['id'])
#         status = order.status.filter(status=StatusEnum.COMPLETED)

#         self.assertTrue(status)

#         # Credit
#         credit = ClientCredit.objects.get(pk=c.credit.id)
#         self.assertEqual(credit.amount, 0.0)


#     """
#     Tests for reservation
#     """

#     """ """
#     def test_reserve_order(self):
#         r = OrderHelper.reserve({
#             'name': 'Test Payment',
#             'comment': '...',

#             'reference': '007',
#             'type': OrderTypeEnum.OFFICE,

#             'payer': self.p1.id,
#             'caster': self.p1.id,

#             'methods': [
#                 {
#                     'amount': 130.0,
#                     'method': MethodEnum.CASH,
#                     'reference': ''
#                 },
#                 {
#                     'amount': 132.0,
#                     'method': MethodEnum.CHECK,
#                     'reference': '000007'
#                 }
#             ],

#             # 262 €
#             'peri': [
#                 {
#                     'product': self.septembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id,
#                         self.c4.id,
#                         self.c5.id,
#                     ]
#                 },
#                 {
#                     'product': self.octobre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id,
#                         self.c3.id
#                     ]
#                 },
#                 {
#                     'product': self.novembre.id,
#                     'children': [
#                         self.c1.id,
#                         self.c2.id
#                     ]
#                 }
#             ],
#             'alsh': [
#                 {
#                     # MINUS 6
#                     'child': self.c2.id,
#                     'products': [
#                         # Q2
#                         self.tous1.id,
#                         self.tous2.id,
#                         self.tous3.id,
#                         self.tous4.id,
#                         self.tous5.id,
#                         # Q1
#                         self.aout1.id,
#                         self.aout2.id,
#                         self.aout3.id,
#                         self.aout4.id,
#                         self.aout5.id,
#                     ],
#                 },
#                 {
#                     'child': self.c3.id,
#                     'products': [
#                         # Q1
#                         self.noel1.id,
#                         self.noel2.id,
#                         self.noel3.id,
#                         self.noel4.id,
#                         self.noel5.id
#                     ],
#                 },
#                 {
#                     'child': self.c4.id,
#                     'products': [
#                         # NE
#                         self.noel1.id,
#                         self.noel2.id,
#                         self.noel3.id,
#                         self.noel4.id,
#                         self.noel5.id
#                     ],
#                 },
#             ]
#         })

#         self.assertEqual(r['status'], 'Success')
#         self.assertTrue(r['order']['id'])

#         order = Order.objects.get(pk=r['order']['id'])
#         status = order.status.filter(status=StatusEnum.RESERVED)

#         self.assertTrue(status)
