import json

from unittest import skip
from datetime import datetime, timedelta

from django.conf import settings
from django.urls import reverse
from django.http.request import QueryDict
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status

from . import BaseViewTest, create_user, create_child, create_order, create_client

from users.utils import _localize

from order.models import Order, StatusEnum, MethodEnum, OrderTypeEnum
from order.utils import OrderHelper as OH

from payment_vads.models import TransactionVADS
from registration.models import Sibling, SiblingIntels, Record

# tests for views

class VerificationBaseTest (BaseViewTest):
    @skip
    def test_active_school_year (self):
        pass

    @skip
    def test_verify_payer_exist (self):
        pass

    @skip
    def test_verify_payer_is_parent (self):
        pass

    @skip
    def test_verify_caster_exist (self):
        pass

    @skip
    def test_verify_caster_is_admin (self):
        pass

    @skip
    def test_parent_no_sibling (self):
        pass

    @skip
    def test_parent_no_intels (self):
        pass
    
    @skip
    def test_product_does_not_exist (self):
        pass

    @skip
    def test_child_is_not_bound (self):
        pass

    @skip
    # Child is in sibling but User does not exist
    def test_child_does_not_exist (self):
        pass

    @skip
    def test_child_has_no_record (self):
        pass

    @skip
    def test_child_has_no_record_classroom (self):
        pass

    @skip
    def test_product_already_bought (self):
        pass

    @skip
    # Product does not fit to child
    def test_p (self):
        pass

    @skip
    def test_stock (self):
        pass


class OrderingBaseTest(BaseViewTest):

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

    def test_verification (self):
        res = OH.verify_order({
            'payer': self.parent.id,
            'caster': self.admin.id,
            'cart': [
                {
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }
            ],
        })

        # print (res)
        self.assertTrue(res['tickets'])
        self.assertFalse(res['tickets_invalid'])

    #
    @skip
    def test_create_order_invalid_cart (self):
        res = self.client.post(
            reverse('api_order_create'),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.UNSET,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'methods': [{
                    'method': MethodEnum.CASH.value,
                    'amount': 20.0,
                    'reference': ''
                }],

                'cart': [{'children': [self.child_1.id]}]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        print (res)
        # print (res.json())

        # data = res.json()

        # self.assertEqual(res.status_code, 400)
        # self.assertEqual(data['message'], 'Création impossible: le panier contient des produits invalides.')

    @skip
    def test_create_order_invalid_form (self):
        pass
    
    #
    def test_create_order_already_exist (self):
        create_order({
            'payer': self.parent.id,
            'caster': self.admin.id,
            'amount': 0.0,

            'status': [StatusEnum.WAITING],
            
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
        })

        try:
            res = OH.create_order({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.UNSET,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'methods': [{
                    'method': MethodEnum.CASH.value,
                    'amount': 20.0,
                    'reference': ''
                }],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            })
        except Exception as e:
            self.assertEqual(str(e), 'Une commande est déjà en cours pour ce parent.')

    #
    def test_create_order_expired (self):
        print ('test_create_order_expired')
        order = create_order({
            'payer': self.parent.id,
            'caster': self.admin.id,
            'amount': 0.0,

            'status': [StatusEnum.WAITING],
            
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
        })

        order.date = _localize('2000-01-01 00:00:00')
        order.save()

        res = OH.create_order({
            'name': 'Test order',
            'comment': '',
            'type': OrderTypeEnum.OFFICE.value,
            'reference': '',
            'caster': self.admin.id,
            'payer': self.parent.id,   

            # 'methods': [{
            #     'method': MethodEnum.CASH.value,
            #     'amount': 20.0,
            #     'reference': ''
            # }],

            'cart': [{
                'children': [self.child_1.id],
                'product': self.septembre.id,
            }]
        })

        self.assertTrue(res['order'])
        self.assertEqual(res['status'], status.HTTP_402_PAYMENT_REQUIRED)

        last_status = res['order'].status.first()
        self.assertEqual(last_status.status, StatusEnum.WAITING)

    # Ensure order is COMPLETED with no methods if product sum is 0
    def test_create_order_amount_0 (self):
        intel = self.sibling.intels.first()
        intel.quotient_1 = 3
        intel.save()

        res = OH.create_order({
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
        })

        self.assertTrue(res['order'])
        self.assertEqual(res['status'], status.HTTP_201_CREATED)

        last_status = res['order'].status.first()
        self.assertEqual(last_status.status, StatusEnum.COMPLETED)

        methods = res['order'].methods.all()
        self.assertFalse(methods)

    # Ensure if method is provided an error 
    # is triggered if amount is incorrect
    def test_create_order_waiting (self):
        create_client(self.parent.id, 20)

        try:
            res = OH.create_order({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'methods': [
                    {
                        'method': MethodEnum.CASH.value,
                        'amount': 10.0,
                        'reference': ''
                    }
                ],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }, is_admin=True)
        except Exception as e:
            self.assertEqual(str(e), 'Montant incorrect. Attendu: 0.0 €.')

    # Ensure if method is provided an error 
    # is triggered if amount is incorrect
    def test_create_order_reserved (self):
        create_client(self.parent.id, 20)

        try:
            res = OH.create_order({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'methods': [
                    {
                        'method': MethodEnum.CASH.value,
                        'amount': 10.0,
                        'reference': ''
                    }
                ],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }, order_status=StatusEnum.RESERVED, is_admin=True)
        except Exception as e:
            self.assertEqual(str(e), 'Montant incorrect. Attendu: 0.0 €.')
   
    # Work
    def test_create_order_waiting_no_method (self):
        res = OH.create_order({
            'name': 'Test order',
            'comment': '',
            'type': OrderTypeEnum.OFFICE.value,
            'reference': '',
            'caster': self.admin.id,
            'payer': self.parent.id,   

            'cart': [{
                'children': [self.child_1.id],
                'product': self.septembre.id,
            }]
        })

        self.assertTrue(res['order'])
        self.assertEqual(res['status'], status.HTTP_402_PAYMENT_REQUIRED)

        last_status = res['order'].status.first()
        self.assertEqual(last_status.status, StatusEnum.WAITING)

    # Work
    def test_create_order_reserved_no_method (self):
        res = OH.create_order({
            'name': 'Test order',
            'comment': '',
            'type': OrderTypeEnum.OFFICE.value,
            'reference': '',
            'caster': self.admin.id,
            'payer': self.parent.id,   

            'cart': [{
                'children': [self.child_1.id],
                'product': self.septembre.id,
            }]
        }, order_status=StatusEnum.RESERVED)

        self.assertTrue(res['order'])
        self.assertEqual(res['status'], status.HTTP_402_PAYMENT_REQUIRED)

        last_status = res['order'].status.first()
        self.assertEqual(last_status.status, StatusEnum.RESERVED)

    # Work
    def test_create_order_reserved_with_credit (self):
        create_client(self.parent.id, 20)

        res = OH.create_order({
            'name': 'Test order',
            'comment': '',
            'type': OrderTypeEnum.OFFICE.value,
            'reference': '',
            'caster': self.admin.id,
            'payer': self.parent.id,   

            'methods': [
                # {
                #     'method': MethodEnum.CASH.value,
                #     'amount': 10.0,
                #     'reference': ''
                # }
            ],

            'cart': [{
                'children': [self.child_1.id],
                'product': self.septembre.id,
            }]
        }, order_status=StatusEnum.RESERVED)

        self.assertTrue(res['order'])
        self.assertEqual(res['status'], status.HTTP_201_CREATED)

        last_status = res['order'].status.first()
        self.assertEqual(last_status.status, StatusEnum.COMPLETED)

    # Work
    def test_create_order_force_completed_with_credit (self):
        create_client(self.parent.id, 20)

        res = OH.create_order({
            'name': 'Test order',
            'comment': '',
            'type': OrderTypeEnum.OFFICE.value,
            'reference': '',
            'caster': self.admin.id,
            'payer': self.parent.id,   

            'cart': [{
                'children': [self.child_1.id],
                'product': self.septembre.id,
            }]
        }, force_completed=True,
        order_status=StatusEnum.RESERVED)

        self.assertTrue(res['order'])
        self.assertEqual(res['status'], status.HTTP_201_CREATED)

        last_status = res['order'].status.first()
        self.assertEqual(last_status.status, StatusEnum.COMPLETED)

    # Exception
    def test_create_order_force_completed_no_method (self):
        try:
            res = OH.create_order({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }, force_completed=True,
            order_status=StatusEnum.RESERVED)

        except Exception as e:
            self.assertEqual(str(e), 'Montant incorrect. Attendu: 20 €.')

    # 
    def test_create_order_force_completed_invalid_amount (self):
        try:
            res = OH.create_order({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,

                'methods': [{
                    'method': MethodEnum.CASH.value,
                    'amount': 10.0,
                    'reference': ''
                }],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }, force_completed=True,
            order_status=StatusEnum.RESERVED, is_admin=True)

        except Exception as e:
            self.assertEqual(str(e), 'Montant incorrect. Attendu: 20 €.')

    #
    def test_create_order_force_completed_correct_amount (self):
        res = OH.create_order({
            'name': 'Test order',
            'comment': '',
            'type': OrderTypeEnum.OFFICE.value,
            'reference': '',
            'caster': self.admin.id,
            'payer': self.parent.id,

            'methods': [{
                'method': MethodEnum.CASH.value,
                'amount': 20.0,
                'reference': ''
            }],

            'cart': [{
                'children': [self.child_1.id],
                'product': self.septembre.id,
            }]
        }, force_completed=True,
        order_status=StatusEnum.RESERVED, is_admin=True)

        self.assertTrue(res['order'])
        self.assertEqual(res['status'], status.HTTP_201_CREATED)

        last_status = res['order'].status.first()
        self.assertEqual(last_status.status, StatusEnum.COMPLETED)

    @skip
    def test_reserve_order_as_admin (self):
        print ('test_reserve_order')
        # create_client(self.parent.id, 20)

        res = self.client.post(
            reverse('api_order_reserve'),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'methods': [
                    {
                        'method': MethodEnum.CASH.value,
                        'amount': 20.0,
                        'reference': ''
                    }
                ],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        # print (res)
        # print (res.json())

        data = res.json()

        self.assertEqual(res.status_code, 402)
        self.assertTrue(data['order'])
        self.assertEqual(data['order']['status'][0]['status'], StatusEnum.RESERVED)

    @skip
    def test_pay_order_as_admin (self):
        print ('test_pay_order')
        # create_client(self.parent.id, 20)

        res = self.client.post(
            reverse('api_order_pay'),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'methods': [
                    {
                        'method': MethodEnum.CASH.value,
                        'amount': 20.0,
                        'reference': ''
                    }
                ],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )

        # print (res)
        # print (res.json())

        data = res.json()

        self.assertEqual(res.status_code, 201)
        self.assertTrue(data['order'])
        self.assertEqual(data['order']['status'][0]['status'], StatusEnum.COMPLETED)


class OrderingBaseTestAsParent(BaseViewTest):

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
            'quotient_2': 0,
            'recipent_number': 0,
        }, self.active_school_year.id)

        self.sibling.add_child(self.child_1.id)

        # Records
        Record.objects.create(
            child=self.child_1.id,
            classroom=1,
            school_year=self.active_school_year.id
        )

    #
    @skip
    def test_create_order_already_exist (self):
        create_order({
            'payer': self.parent.id,
            'caster': self.admin.id,
            'amount': 0.0,

            'status': [StatusEnum.WAITING],
            
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
        })

        res = self.client.post(
            reverse('api_order_create'),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.UNSET,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'methods': [{
                    'method': MethodEnum.CASH.value,
                    'amount': 20.0,
                    'reference': ''
                }],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        # print (res)
        # print (res.json())

        data = res.json()

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['message'], 'Une commande est déjà en cours pour ce parent.')

    #
    @skip
    def test_create_order_expired_as_parent (self):
        print ('test_create_order_expired')
        order = create_order({
            'payer': self.parent.id,
            'caster': self.admin.id,
            'amount': 0.0,

            'status': [StatusEnum.WAITING],
            
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
        })

        order.date = _localize('2000-01-01 00:00:00')
        order.save()

        res = self.client.post(
            reverse('api_order_create'),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                # 'methods': [{
                #     'method': MethodEnum.CASH.value,
                #     'amount': 20.0,
                #     'reference': ''
                # }],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        # print (res)
        # print (res.json())

        data = res.json()

        self.assertEqual(res.status_code, 402)
        self.assertTrue(data['order'])

    #
    @skip
    def test_create_order_with_credit_as_parent (self):
        print ('test_create_order_with_credit_as_parent')
        create_client(self.parent.id, 20)

        res = self.client.post(
            reverse('api_order_create'),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'methods': [
                    # {
                    #     'method': MethodEnum.CASH.value,
                    #     'amount': 10.0,
                    #     'reference': ''
                    # }
                ],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        # print (res)
        # print (res.json())

        data = res.json()

        self.assertEqual(res.status_code, 201)
        self.assertTrue(data['order'])

    @skip
    def test_reserve_order_as_parent (self):
        print ('test_reserve_order_as_parent')
        # create_client(self.parent.id, 20)

        res = self.client.post(
            reverse('api_order_reserve'),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'methods': [
                    {
                        'method': MethodEnum.CASH.value,
                        'amount': 20.0,
                        'reference': ''
                    }
                ],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        print (res)
        print (res.json())

        data = res.json()

        self.assertEqual(res.status_code, 403)
        # self.assertTrue(data['order'])
        # self.assertEqual(data['order']['status'][0]['status'], StatusEnum.RESERVED)

    @skip
    def test_pay_order_as_parent (self):
        print ('test_pay_order_as_parent')
        # create_client(self.parent.id, 20)

        res = self.client.post(
            reverse('api_order_pay'),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'methods': [
                    {
                        'method': MethodEnum.CASH.value,
                        'amount': 20.0,
                        'reference': ''
                    }
                ],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )

        # print (res)
        # print (res.json())

        data = res.json()

        self.assertEqual(res.status_code, 403)
        # self.assertTrue(data['order'])
        # self.assertEqual(data['order']['status'][0]['status'], StatusEnum.COMPLETED)

    
class InstantPaymentTest(BaseViewTest):

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

    def test_pay_no_credit_no_methods (self):
        res = self.client.post(
            reverse('api_order_pay_instant'),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 400)

        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Montant incorrect. Attendu: 20 €.')

    # 
    def test_pay_incorrect_amount (self):
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
                    'method': MethodEnum.CASH.value,
                    'amount': 10.0,
                    'reference': ''
                }],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 400)

        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Montant incorrect. Attendu: 20 €.')

    #
    def test_pay_with_credit_no_methods (self):
        create_client(self.parent.id, 20)

        res = self.client.post(
            reverse('api_order_pay_instant'),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 201)
        self.assertTrue(data['order'])

        last_status = data['order']['status'][0]
        self.assertEqual(last_status['status'], StatusEnum.COMPLETED)

    #
    def test_pay_completed (self):
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
                    'method': MethodEnum.CASH.value,
                    'amount': 20.0,
                    'reference': ''
                }],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 201)

        self.assertEqual(data['status'], 'Success')
        self.assertTrue(data['order'])

        last_status = data['order']['status'][0]
        self.assertEqual(last_status['status'], StatusEnum.COMPLETED)


class ConfirmAndReserveTest (BaseViewTest):
    
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

    # Ensure if method is provided an error 
    # is triggered if amount is incorrect
    def test_confirm_with_method (self):
        create_client(self.parent.id, 20)

        res = self.client.post(
            reverse('api_order_confirm'),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'methods': [{
                    'method': MethodEnum.CASH.value,
                    'amount': 10.0,
                    'reference': ''
                }],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 400)

        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Aucune méthode de paiement requise.')

    # Work
    def test_reserve_with_credit (self):
        create_client(self.parent.id, 20)

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
                    'product': self.septembre.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 201)

        self.assertTrue(data['order'])
        self.assertEqual(data['status'], 'Success')

        last_status = data['order']['status'][0]
        self.assertEqual(last_status['status'], StatusEnum.COMPLETED)

    #
    def test_reserve_partial_credit (self):
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
                    'product': self.septembre.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 402)

        self.assertTrue(data['order'])
        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['order']['amount_rcvd'], 10)

        last_status = data['order']['status'][0]
        self.assertEqual(last_status['status'], StatusEnum.RESERVED)

    #
    def test_reserve_success (self):
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
                    'product': self.septembre.id,
                }]
            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 402)

        self.assertTrue(data['order'])
        self.assertEqual(data['status'], 'Success')
        self.assertEqual(data['order']['amount_rcvd'], 0)

        last_status = data['order']['status'][0]
        self.assertEqual(last_status['status'], StatusEnum.RESERVED)

    @skip
    def test_confirm_order_with_credit (self):
        pass

    @skip
    def test_confirm_order (self):
        pass

    @skip
    def test_reservation_order (self):
        pass
    
    ### From Base
    # Ensure if method is provided an error 
    # is triggered if amount is incorrect
    @skip
    def test_reserve_with_method (self):
        create_client(self.parent.id, 20)

        try:
            res = OH.create_order({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

                'methods': [
                    {
                        'method': MethodEnum.CASH.value,
                        'amount': 10.0,
                        'reference': ''
                    }
                ],

                'cart': [{
                    'children': [self.child_1.id],
                    'product': self.septembre.id,
                }]
            }, order_status=StatusEnum.RESERVED)
        except Exception as e:
            self.assertEqual(str(e), 'Montant incorrect. Attendu: 20 €.')
   
    # Work
    @skip
    def test_create_order_waiting_no_method (self):
        res = OH.create_order({
            'name': 'Test order',
            'comment': '',
            'type': OrderTypeEnum.OFFICE.value,
            'reference': '',
            'caster': self.admin.id,
            'payer': self.parent.id,   

            'cart': [{
                'children': [self.child_1.id],
                'product': self.septembre.id,
            }]
        })

        self.assertTrue(res['order'])
        self.assertEqual(res['status'], status.HTTP_402_PAYMENT_REQUIRED)

        last_status = res['order'].status.first()
        self.assertEqual(last_status.status, StatusEnum.WAITING)

    # Work
    @skip
    def test_create_order_reserved_no_method (self):
        res = OH.create_order({
            'name': 'Test order',
            'comment': '',
            'type': OrderTypeEnum.OFFICE.value,
            'reference': '',
            'caster': self.admin.id,
            'payer': self.parent.id,   

            'cart': [{
                'children': [self.child_1.id],
                'product': self.septembre.id,
            }]
        }, order_status=StatusEnum.RESERVED)

        self.assertTrue(res['order'])
        self.assertEqual(res['status'], status.HTTP_402_PAYMENT_REQUIRED)

        last_status = res['order'].status.first()
        self.assertEqual(last_status.status, StatusEnum.RESERVED)


class PaymentTest(BaseViewTest):

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

    def test_order_no_payload (self):
        res = self.client.post(
            reverse('api_order_pay', kwargs={'pk': 1}),
            json.dumps({}),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 400)
        
        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Payload vide.')

    def test_order_invalid_payload (self):
        order = create_order({
            'payer': self.parent.id,
            'caster': self.admin.id,
            'amount': 20.0,

            'status': [StatusEnum.WAITING],
            
            'methods': [],

            'tickets': [{
                'payee': self.child_1.id,
                'price': 20,
                'product': self.septembre.id,
            }]
        })

        res = self.client.post(
            reverse('api_order_pay', kwargs={'pk': order.id}),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 400)
        
        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Payload incorrect.')

    def test_order_does_not_exist (self):
        res = self.client.post(
            reverse('api_order_pay', kwargs={'pk': 9999}),
            json.dumps({
                'name': 'Test order',
                'comment': '',
                'type': OrderTypeEnum.OFFICE.value,
                'reference': '',
                'caster': self.admin.id,
                'payer': self.parent.id,   

            }),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 404)
        
        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Reçu introuvable.')

    def test_order_invalid_status (self):
        order = create_order({
            'payer': self.parent.id,
            'caster': self.admin.id,
            'amount': 20.0,

            'status': [StatusEnum.COMPLETED],
            
            'methods': [],

            'tickets': [{
                'payee': self.child_1.id,
                'price': 20,
                'product': self.septembre.id,
            }]
        })

        res = self.client.post(
            reverse('api_order_pay', kwargs={'pk': order.id}),
            json.dumps([{
                'method': MethodEnum.CASH.value,
                'amount': 20.0,
                'reference': ''
            }]),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 400)
        
        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Impossible de payer le reçu avec le status actuel.')

    def test_order_invalid_amount (self):
        order = create_order({
            'payer': self.parent.id,
            'caster': self.admin.id,
            'amount': 20.0,
            'amount_rcvd': 0.0,

            'status': [StatusEnum.RESERVED],
            
            'methods': [],

            'tickets': [{
                'payee': self.child_1.id,
                'price': 20,
                'product': self.septembre.id,
            }]
        })

        res = self.client.post(
            reverse('api_order_pay', kwargs={'pk': order.id}),
            json.dumps([{
                'method': MethodEnum.CASH.value,
                'amount': 10.0,
                'reference': ''
            }]),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 400)
        
        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Montant incorrect. Attendu: 20.0 €.')

    def test_order_partial_amount (self):
        order = create_order({
            'payer': self.parent.id,
            'caster': self.admin.id,
            'amount': 20.0,
            'amount_rcvd': 10.0,

            'status': [StatusEnum.RESERVED],
            
            'methods': [],

            'tickets': [{
                'payee': self.child_1.id,
                'price': 20,
                'product': self.septembre.id,
            }]
        })

        res = self.client.post(
            reverse('api_order_pay', kwargs={'pk': order.id}),
            json.dumps([{
                'method': MethodEnum.CASH.value,
                'amount': 20.0,
                'reference': ''
            }]),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 400)
        
        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Montant incorrect. Attendu: 10.0 €.')

    def test_pay_cash_and_check_parent (self):
        # print ('test_pay_cash_and_check_parent')
        
        order = create_order({
            'payer': self.parent.id,
            'caster': self.admin.id,
            'amount': 20.0,
            'amount_rcvd': 0.0,

            'status': [StatusEnum.WAITING],
            
            'methods': [],

            'tickets': [{
                'payee': self.child_1.id,
                'price': 20,
                'product': self.septembre.id,
            }]
        })

        res = self.client.post(
            reverse('api_order_pay', kwargs={'pk': order.id}),
            json.dumps([
                {
                    'method': MethodEnum.CASH.value,
                    'amount': 20.0,
                    'reference': ''
                },
                {
                    'method': MethodEnum.CHECK.value,
                    'amount': 20.0,
                    'reference': ''
                }
            ]),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 403)
        
        self.assertEqual(data['status'], 'Failure')
        self.assertEqual(data['message'], 'Méthode de paiement non autorisée.')

    def test_order_success (self):
        order = create_order({
            'payer': self.parent.id,
            'caster': self.admin.id,
            'amount': 20.0,
            'amount_rcvd': 0.0,

            'status': [StatusEnum.WAITING],
            
            'methods': [],

            'tickets': [{
                'payee': self.child_1.id,
                'price': 20,
                'product': self.septembre.id,
            }]
        })

        res = self.client.post(
            reverse('api_order_pay', kwargs={'pk': order.id}),
            json.dumps([{
                'method': MethodEnum.CASH.value,
                'amount': 20.0,
                'reference': ''
            }]),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.admin.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 200)
        
        self.assertEqual(data['status'], 'Success')
        self.assertTrue(data['order'])

        last_status = data['order']['status'][0]
        self.assertEqual(last_status['status'], StatusEnum.COMPLETED)

    def test_order_success_as_parent (self):
        order = create_order({
            'payer': self.parent.id,
            'caster': self.admin.id,
            'amount': 20.0,
            'amount_rcvd': 0.0,

            'status': [StatusEnum.WAITING],
            
            'methods': [],

            'tickets': [{
                'payee': self.child_1.id,
                'price': 20,
                'product': self.septembre.id,
            }]
        })

        res = self.client.post(
            reverse('api_order_pay', kwargs={'pk': order.id}),
            json.dumps([{
                'method': MethodEnum.ONLINE.value,
                'amount': 20.0,
                'reference': ''
            }]),
            content_type='application/json',
            HTTP_Authorization=f'Bearer {self.parent.auth.token}'
        )
        
        data = res.json()

        self.assertEqual(res.status_code, 200)
        
        self.assertEqual(data['status'], 'Success')
        self.assertTrue(data['order'])

        last_status = data['order']['status'][0]
        self.assertEqual(last_status['status'], StatusEnum.COMPLETED)


class OrderingIPNTest (BaseViewTest):

    base_payload = {'vads_amount': ['6000'], 'vads_auth_mode': ['FULL'], 'vads_auth_number': ['232958'], 'vads_auth_result': ['00'], 'vads_capture_delay': ['0'], 'vads_card_brand': ['CB'], 'vads_card_number': ['523718XXXXXX2424'], 'vads_payment_certificate': ['d5de8f546b0fd449f4d375385f64ec404f217b23'], 'vads_ctx_mode': ['PRODUCTION'], 'vads_currency': ['978'], 'vads_effective_amount': ['100'], 'vads_effective_currency': ['978'], 'vads_site_id': ['38529398'], 'vads_trans_date': ['20210127160155'], 'vads_trans_id': ['981934'], 'vads_trans_uuid': ['df1d8b12cb4c4664aec4daeeb80f0785'], 'vads_validation_mode': ['0'], 'vads_version': ['V2'], 'vads_warranty_result': ['YES'], 'vads_payment_src': ['EC'], 'vads_cust_email': ['jessica.clement.972@orange.fr'], 'vads_tid': ['001'], 'vads_sequence_number': ['1'], 'vads_acquirer_network': ['CB'], 'vads_contract_used': ['5254450'], 'vads_trans_status': ['AUTHORISED'], 'vads_expiry_month': ['1'], 'vads_expiry_year': ['2023'], 'vads_bank_code': ['19806'], 'vads_bank_label': ['Caisse r\xc3\xa9gionale de cr\xc3\xa9dit agricole mutuel de la Martinique'], 'vads_bank_product': ['TCS'], 'vads_pays_ip': ['FR'], 'vads_presentation_date': ['20210127160155'], 'vads_effective_creation_date': ['20210127160155'], 'vads_operation_type': ['DEBIT'], 'vads_result': ['00'], 'vads_extra_result': [''], 'vads_card_country': ['FR'], 'vads_language': ['fr'], 'vads_brand_management': ['{"userChoice":false,"brandList":"CB|MASTERCARD","brand":"CB"}'], 'vads_hash': ['b069522f949aee10ac6e69524608887a28ff3ba48cfe131605359142f4bb4693'], 'vads_url_check_src': ['BO'], 'vads_ext_info_Param\xc3\xa8tres': ['?v=1!pid=0!p=199,36!p=200,36!p=201,36'], 'vads_threeds_enrolled': ['Y'], 'vads_threeds_auth_type': ['CHALLENGE'], 'vads_threeds_eci': ['02'], 'vads_threeds_xid': ['Q2FaR2hGTHRuWEFNT1NYS0huNlY='], 'vads_threeds_cavvAlgorithm': ['3'], 'vads_threeds_status': ['Y'], 'vads_threeds_sign_valid': ['1'], 'vads_threeds_error_code': [''], 'vads_threeds_exit_status': ['10'], 'vads_threeds_cavv': ['jG/a1nqLyJNfAAVgEY8lcmSNIKY='], 'signature': ['b0KhRU0wvEyjMfyJXj2Bt8ZH6DhlBvfAT2m5/iwn/XQ=']}

    @skip
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

    @skip
    def test_transaction_creation_error (self):
        pass

    @skip
    def test_parsed_return_false (self):
        pass

    @skip
    def test_form_error (self):
        pass

    @skip
    def test_incorrect_amount (self):
        pass
    
    @skip
    def test_lazy (self):
        print ('test_lazy')

        print (self.parent.id)
        print (self.child_1.id)
        print (self.septembre.id)

        self.base_payload['vads_ext_info_ParamÃ¨tres'][0] = self.base_payload['vads_ext_info_ParamÃ¨tres'][0].replace('pid=0', f'pid={self.parent.id}')

        res = self.client.post(
            reverse('api_vads_ipn'),
            json.dumps(self.base_payload),
            content_type='application/json'
        )

        data = res.json()

        print (res)
        print (data)

        transaction = TransactionVADS.objects.last()
        order = Order.objects.get(pk=transaction.order_id)
        order_status = order.status.first()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(transaction.order_status, 20)
        self.assertEqual(order_status.status, StatusEnum.COMPLETED)



