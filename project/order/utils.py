import sys
import copy
import json
import pytz
import requests

from datetime import datetime, timedelta

from django.db import transaction, models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured
from django.http import QueryDict
from django.utils.timezone import now

from rest_framework import status

from .forms import OrderForm, OrderMethodForm
from .models import Order, Ticket, OrderMethod, OrderStatus, TicketStatus, StatusEnum, MethodEnum, OrderTypeEnum, StatusEnum, _localize

from accounting.models import Client, ClientCreditHistory, HistoryTypeEnum as HTE
from accounting.utils import update_credit

from params.models import Product, SchoolYear
from registration.models import Sibling, SiblingIntels, Record

from users.models import User
from users.utils import _localize

from users.exceptions import InternalErrorException, BadRequestException, NotFoundException, UnauthorizedException, ForbiddenException, FormValidationException

# NAME = 'UPEEM - ALSH&PERI'
# DESCRIPTION = 'Paiement ALSH/PERI 2019-2020'

NAME = 'Paiement ALSH/PERI 2020-2021'

M3 = 0      # Less than 3yo
M6 = 1      # Less than 6yo
P6 = 2      # Plus than 6yo
NE = 0      # Non eligible
Q2 = 1      # Quotient 2
Q1 = 2      # Quotient 1

TARIFS_ALSH = [
    [17],           # M3
    [17, 4, 0],     # M6
    [20, 7, 2],     # P6
]

TARIFS_PERI = [20, 32, 40, 60]

# Verify last parent orders if order 
def verify_payer_orders (payer):
    """
    Raise exception if order in progress
    Cancel if expired and return True
    Return True if orders status are allowed

    Parameters
    ----------
    Payer/Parent PK

    Exceptions
    ----------
    BadRequestException
    """
    ALLOWED_ORDER_STATUS = [
        StatusEnum.COMPLETED, 
        StatusEnum.CANCELED,
        StatusEnum.REFUNDED,
        StatusEnum.CREDITED,
    ]

    last_order = Order.objects.filter(payer=payer).last()
    if last_order:

        # Status check
        last_status = last_order.status.first()
        if last_status.status not in ALLOWED_ORDER_STATUS:

            # Expiration check
            if last_order.has_expired():
                # cancel
                pass
            else:
                raise BadRequestException('Une commande est déjà en cours pour ce parent.')
    
    return True


def create_methods (data, is_admin=False): 
    ALLOWED_METHODS = [
        MethodEnum.ONLINE,
        MethodEnum.ONLINE_VADS,
    ]

    methods = []
    amount_rcvd = 0
    for m in data:
        mf = OrderMethodForm(m)
        if not mf.is_valid():
            raise FormValidationException(mf.errors)
        
        if not is_admin and mf.cleaned_data['method'] not in ALLOWED_METHODS:
            raise ForbiddenException('Méthode de paiement non autorisée.')

        amount = float(mf.cleaned_data['amount'])
        amount_rcvd += amount

        methods.append(OrderMethod(
            amount=amount,
            method=mf.cleaned_data['method'],
            reference=mf.cleaned_data['reference']
        ))

    return methods, amount_rcvd


def cancel_order (client, caster, order_pk=None, tickets_pks=None, type=None):
    """
    Description
    -----------
    Global function for cancel/credit order/tickets
    order_pk or tickets_pks must be passed
    Cannot CREDIT WAITING tickets

    Parameters
    ----------
    data => object {
        client => id
        order_id => id
    }

    Steps
    -----
    Get order
    Get tickets
    Run cancel_tickets func
    """
    try:
        if order_pk:
            order = Order.objects.get(pk=order_pk)
            tickets = order.tickets.all()
            
            if type is None:
                type = HTE.ORDER_CANCELATION.value

        elif tickets_pks:
            order = Order.objects.get(tickets__pk=tickets_pks[0])
            tickets = Ticket.objects.filter(id__in=tickets_pks)

            # Check ticket 
            # clean_tickets_ids = [ticket.id for ticket in tickets]
            # for ticket_pk in tickets_pks:
            #     if ticket_pk not in clean_tickets_ids:

            for ticket in tickets:
                if ticket.order.id != order.id:
                    raise BadRequestException(f'Le ticket ({ticket.id}) n\'appartient pas à ce reçu.')

            type = HTE.TICKET_CANCELATION.value

        else:
            raise BadRequestException('Aucun reçu/ticket à annuler.')
    
    except Order.DoesNotExist:
        raise NotFoundException('Reçu introuvable.')
    
    except BadRequestException as e:
        raise e

    except Exception as e:
        # print (e)
        raise BadRequestException('Payload incorrect.')

    if order.payer != client:
        raise ForbiddenException('Ce reçu n\'appartient pas à ce parent.')

    CANCEL_STATUS = [
        StatusEnum.WAITING,
        StatusEnum.RESERVED
    ]

    CREDIT_STATUS = [
        StatusEnum.COMPLETED
    ]

    last_status = order.status.first()

    if last_status:
        if last_status.status in CANCEL_STATUS:
            if order_pk:
                return cancel_tickets(
                    order, 
                    tickets,
                    type,
                    caster
                )
            else:
                raise BadRequestException('Impossible d\'annuler un ticket en attente.')

        elif last_status.status in CREDIT_STATUS:
            return credit_tickets(
                order,
                tickets,
                type,
                caster
            )

        else:
            raise BadRequestException('Status du reçu non géré.')
    
    else:
        raise BadRequestException('Aucun status trouvé sur ce reçu.')


def cancel_tickets (order, tickets, type, caster):
    canceled = 0
    cancel_status = []

    # Cache for products
    products = {}

    for ticket in tickets:
        
        try:
            if ticket.product not in products: 
                product = Product.objects.get(pk=ticket.product)
                products[ticket.product] = product

            else:
                product = products[ticket.product]

        except Product.DoesNotExist:
            cancel_status.append(f'Erreur: le produit ({ticket.product}) du ticket ({ticket.id}) n\'existe pas.')
            continue

        ALLOWED_STATUS = [
            StatusEnum.WAITING,
            StatusEnum.RESERVED
        ]

        status = ticket.status.first()
        if status:
            if status.status in ALLOWED_STATUS:
                canceled += 1
                ticket._add_status(StatusEnum.CANCELED)
                cancel_status.append(f'Information: le ticket ({ticket.id}) sera annulé.')

                # Stock
                product.stock_current -= 1
                product.save()

            else:
                cancel_status.append(f'Erreur: status non géré sur le ticket ({ticket.id}), il ne sera pas annulé.')

        else:
            cancel_status.append(f'Erreur: status non géré sur le ticket ({ticket.id}), il ne sera pas annulé.')
        
    # Technically all tickets should have been canceled
    if order.amount_rcvd:
        status = update_credit(
            order.payer,
            {
                'type': type,
                'credit': order.amount_rcvd,
                'caster': caster,
                'comment': ''
            }
        )

        if status['status'] == 'Success':
            cancel_status.append(f'Information: tous les tickets ont été annulé, ce reçu sera annulé.')
            order._add_status(StatusEnum.CREDITED)

        elif status['status'] == 'Failure':
            cancel_status = [f'Erreur: l\'annulation à échouer avec le message: {status["message"]}.']
            print (status)

    else:
        cancel_status.append(f'Information: tous les tickets ont été annulé, ce reçu sera annulé.')
        order._add_status(StatusEnum.CANCELED)

    return cancel_status


def credit_tickets (order, tickets, type, caster):
    """
    Parameters
    ----------
    data => object {
        client => id
        tickets => list of ids - Only in the same order
    }

    Steps
    -----
    Get client data/create if not
    Get sibling
        Store children IDs
    Get order ID from 1st ticket
    Verify tickets
        Get siblings
        Get tickets
        Check payee id
        Increase refound amount
        Set it as CANCELED
    Update client account
    """

    # Get tickets
    # And check payee
    amount = 0
    cancel_status = []

    # Cache for products
    products = {}
    to_cancel = []

    for ticket in tickets:
        
        try:
            if ticket.product not in products: 
                product = Product.objects.get(pk=ticket.product)
                products[ticket.product] = product

            else:
                product = products[ticket.product]

        except Product.DoesNotExist:
            cancel_status.append(f'Erreur: le produit ({ticket.product}) du ticket ({ticket.id}) n\'existe pas.')
            continue

        ALLOWED_STATUS = [
            StatusEnum.COMPLETED
        ]

        status = ticket.status.first()

        if status.status in ALLOWED_STATUS:
            amount += ticket.price
            to_cancel.append(ticket)
            cancel_status.append(f'Information: le ticket ({ticket.id}) sera crédité.')

        else:
            cancel_status.append(f'Erreur: status non géré sur le ticket ({ticket.id}), il ne sera pas crédité.')
        
    # 1.5.3
    if amount:
        status = update_credit(
            order.payer,
            {
                'type': type,
                'credit': amount,
                'caster': caster,
                'comment': ''
            }
        )

        if status['status'] == 'Success':
            for ticket in to_cancel:
                ticket._add_status(StatusEnum.CREDITED)

                # Stock
                products[ticket.product].stock_current -= 1
                products[ticket.product].save()

            if len(to_cancel) == len(order.tickets.all()):
                cancel_status.append(f'Information: tous les tickets ont été crédité, ce reçu sera crédité.')
                order._add_status(StatusEnum.CREDITED)

        elif status['status'] == 'Failure':
            cancel_status = [f'Erreur: l\'annulation à échouer avec le message: {status["message"]}.']
            print (status)

    else:
        for ticket in to_cancel:
            ticket._add_status(StatusEnum.CANCELED)

            # Stock
            products[ticket.product].stock_current -= 1
            products[ticket.product].save()

        if len(to_cancel) == len(order.tickets.all()):
            cancel_status.append(f'Information: tous les tickets ont été annulé, ce reçu sera annulé.')
            order._add_status(StatusEnum.CANCELED)

    return cancel_status


class OrderHelper:

    @staticmethod
    def verify_order (data, soft=False):
        """
        PAYLOAD {
            payer: int
            caster: int
            peri: dict
            alsh: dict
        }
        Raises
        ------
        BadRequestException
        """
        try:
            verify_result = OrderHelper.Verifications._verify(data)

            if soft:
                return verify_result

            # If hard
            client = Client.objects.get(pk=data['payer'])
            credit = client.credit
        
            if credit > verify_result['amount']:
                verify_result['amount'] = 0

            else:
                verify_result['amount'] = verify_result['amount'] - credit
                
        except ObjectDoesNotExist:
            pass
                
        # If client does not exist return normal amount
        except Exception as e:
            raise e

        return verify_result

    """
    NOTE
        check if product is unique for every children in peri/alsh 
    """
    class Verifications:

        @staticmethod
        def _has_bought(child, product):
            ts = Ticket.objects.filter(
                payee=child,
                product=product
            ).all()

            for t in ts:
                status = t.status.first()
                if status.status == StatusEnum.COMPLETED or status.status == StatusEnum.RESERVED:
                    return True
            return False

        """ 
        Return an age for a given date (in string) and start point (mod) 
        if mod is None ...
        """
        @staticmethod
        def _get_age_from_str(date_str, mod=None):
            if mod:
                today = datetime.strptime(mod, '%Y-%m-%d')
            else:
                today = datetime.now()
            birthDate = datetime.strptime(date_str, '%Y-%m-%d')

            age = today.year - birthDate.year
            m = today.month - birthDate.month

            if m < 0 or (m == 0 and today.day < birthDate.day):
                age -= 1

            return age

        """
        Return an age for a given date and start point(mod)
        if mod is None ...
        """
        @staticmethod
        def _get_age_from_date(birthDate, today=None):
            if not today:
                today = datetime.now()

            age = today.year - birthDate.year
            m = today.month - birthDate.month

            if m < 0 or (m == 0 and today.day < birthDate.day):
                age -= 1

            return age


        """ 
        PAYLOAD {
            payer: int
            caster: int
            peri: dict
            alsh: dict
        }
        
        RETURN FAILURE {
            status: str
            message: str
        }

        RETURN SUCCESS {
            status: str
            amount: float
            tickets: list
            tickets_invalid: list
        }
        """
        @staticmethod
        def _verify(data):
            """
            NOTE - Check same products in payload
            """
            # Gather data to prevent index errors
            try:
                payer_id = data['payer']
                caster_id = data['caster']

                cart = data['cart']

            except KeyError as e:
                raise BadRequestException('Payload invalide. Erreur clé ({}).'.format(str(e)))

            if not cart:
                raise BadRequestException('Le panier est vide.')

            # Gather payer intels
            parent = OrderHelper.Verifications._verify_payer(payer_id)

            # Gather caster intels if different
            if payer_id != caster_id:
                caster = OrderHelper.Verifications._verify_caster(caster_id)
            else:
                caster = None

            # Start PERI and ALSH check
            amount = 0

            tickets = []
            tickets_invalid = []

            try:
                amount, tickets, tickets_invalid = OrderHelper.Verifications._verify_cart(
                    payer_id, cart
                )

            except Exception as e:
                print ('1')
                print (str(e))
                raise BadRequestException(e)

            verify_result = {}
            verify_result['amount'] = amount
            verify_result['tickets'] = tickets
            verify_result['tickets_invalid'] = tickets_invalid

            # if not verify_result['tickets']:
            #     raise BadRequestException('Aucun produit valide.')
                # raise FormValidationException(tickets_invalid)

            return verify_result


        @staticmethod
        def _verify_payer(payer_id):
            try:
                parent = User.objects.get(id=payer_id)

            except User.DoesNotExist:
                raise BadRequestException('Parent introuvable avec l\'ID ({}).'.format(payer_id))

            # Check Role
            for role in parent.roles.all():
                if role.slug == 'parent':
                    return parent
            
            raise BadRequestException('Le payeur n\' est pas un parent.') 


        @staticmethod
        def _verify_caster(caster_id):
            try:
                caster = User.objects.get(id=caster_id)
            except User.DoesNotExist:
                raise BadRequestException('Casteur introuvable avec l\'ID ({}).'.format(payer_id))

            # Role
            for role in caster.roles.all():
                if role.slug == 'admin' or role.slug == 'ap_admin':
                    return caster
            
            raise BadRequestException('Le casteur n\' est pas un administrateur.')


        """ New """
        """ Sum up PERI and ALSH """
        @staticmethod
        def _verify_cart(payer_id, cart):
            try:
                sy = SchoolYear.objects.get(is_active=True)
                products = sy.products.all()
                
                sibling = Sibling.objects.get(parent=payer_id)
                intel = sibling.intels.get(school_year=sy.id)

            except SchoolYear.DoesNotExist:
                raise Exception ('Aucune année scolaire active.')

            except Sibling.DoesNotExist:
                raise Exception ('Aucune parenté trouvé pour ce payeur ({})'.format(payer_id))

            except SiblingIntels.DoesNotExist:
                raise Exception ('Aucun dossier familiale trouvé pour ce payeur ({})'.format(payer_id))

            # Children
            children = {}
            children_sibling = [sc.child for sc in sibling.children.all()]

            amount = 0
            final_cart = {}
            
            tickets = []
            tickets_invalid = []

            def macro_final_cart (product_id, category, child_id):
                if product_id not in final_cart:
                    final_cart[product_id] = {
                        'category': category,
                        'children': []
                    }
                if not child_id in final_cart[product_id]['children']:
                    final_cart[product_id]['children'].append(child_id)
                

            for item in cart:
                # print (item)

                try:
                    product = products.get(pk=item['product'])
                    product_id = item['product']

                    children_ids = item['children']
                except Product.DoesNotExist:
                    tickets_invalid.append({
                        'payee': -1,
                        'product': item['product'],
                        'obs': 'Le produit n\'existe pas.'
                    })
                    continue
                except KeyError as e:
                    raise BadRequestException('Payload invalide. Erreur clé ({}) dans \'cart\'.'.format(str(e)))

                # Check there are children
                if not children_ids:
                    tickets_invalid.append({
                        'payee': -1,
                        'product': item['product'],
                        'obs': 'Aucun enfant pour ce produit.'
                    })
                    continue

                # Check product category
                # ...
                # unknow category
                if product.category == 0:
                    tickets_invalid.append({
                        'payee': -1,
                        'product': item['product'],
                        'obs': 'Le produit n\'appartient à aucune catégorie.'
                    })
                    continue
                
                # PERI - ALSH Commons verifications
                # sibling
                # has bought ?
                # child/record
                # age by product subcat
                # 
                else:
                    # print ('product: ' + str(product_id))
                    # print (children_ids)

                    for child_id in children_ids:
                        # print ('child: ' + str(child_id))
                        # Children list
                        # None for a blacklisted (child/record/sibling unknown/invalid)
                        # Dict for a valid child
                        # ...                        
                        # Check child is a valid user
                        # Check record is valid (sy)
                        # Add child to children
                        if child_id not in children:

                            # Check child is in sibling
                            if not child_id in children_sibling:
                                tickets_invalid.append({
                                    'payee': child_id,
                                    'product': -1,
                                    'obs': 'Cet enfant n\'est pas lié au payeur.'
                                })
                                children[child_id] = None
                                continue

                            child = None
                            record = None
                            try:
                                child = User.objects.get(id=child_id)
                                record = Record.objects.get(child=child_id, school_year=sy.id)
                            except User.DoesNotExist:
                                tickets_invalid.append({
                                    'payee': child_id,
                                    'product': -1,
                                    'obs': 'Enfant introuvable.'
                                })
                            except Record.DoesNotExist:
                                tickets_invalid.append({
                                    'payee': child_id,
                                    'product': -1,
                                    'obs': 'Aucune inscription active pour cet enfant.'
                                })

                            finally:
                                if not child or not record:
                                    children[child_id] = None
                                    continue

                                if not record.classroom:
                                    tickets_invalid.append({
                                        'payee': child_id,
                                        'product': -1,
                                        'obs': 'Classe scolaire non renseignée.'
                                    })
                                    children[child_id] = None
                                    continue
                                
                                children[child_id] = {
                                    'dob': child.dob,
                                    'subcategory': 1 if record.classroom > 0 and record.classroom < 5 else 2
                                }

                                # print ('finally')

                        # Check child never bought product
                        if OrderHelper.Verifications._has_bought(child_id, product_id):
                            tickets_invalid.append({
                                'payee': child_id,
                                'product': product_id,
                                'obs': 'Produit déjà réservé.'
                            })
                            continue

                        # print ('a')

                        # PERI
                        # No more verification
                        # Add child to final cart
                        if product.category == 1:
                            child = children[child_id]
                            if not child:
                                continue

                            macro_final_cart(product_id, 1, child_id)

                        # ALSH
                        # Further verifications
                        # Add child to final cart
                        else:
                            child = children[child_id]
                            if not child:
                                continue

                            if child['subcategory'] != product.subcategory:
                                tickets_invalid.append({
                                    'payee': child_id,
                                    'product': product_id,
                                    'obs': 'Le product ne correspond pas à l\'âge de l\'enfant.'
                                })
                                continue

                            macro_final_cart(product_id, 2, child_id)

                        # print ('b')
                        

            # print ('3')
            for key in final_cart:
                item = final_cart[key]

                count = len(item['children'])
                if not count:
                    continue

                # PERI
                if item['category'] == 1:
                    index = min(count, len(TARIFS_PERI))
                    # print (index)

                    # July exception
                    if key != 1011:
                        amount += TARIFS_PERI[index - 1]

                    # print ('index: ', index)
                    # print ('amount: ', amount)

                    for child_id in item['children']:
                        price = TARIFS_PERI[index - 1] / count
                        # price = round(TARIFS_PERI[index - 1] / count)

                        # July exception
                        if key == 1011:
                            price = 5.0
                            amount += price

                        tickets.append({
                            'payee': child_id,
                            'price': price,
                            'product': key
                        })

                # ALSH
                else:
                    product = products.get(pk=key)

                    # if product.stock_max != 0:
                    lenc = len(item['children'])

                    left = product.stock_max - product.stock_current

                    # print ('# Stock')
                    # print (key)
                    # print (lenc)
                    # print (left)

                    if lenc > left and product.stock_max != 0:
                        tickets_invalid.append({
                            'payee': -1,
                            'product': key,
                            'obs': 'Place manquante.' # ({} restant(s)).'.format(left)
                        })
                    else:
                        for child_id in item['children']:
                            if not child_id in children:
                                continue

                            child = children[child_id]

                            if OrderHelper.Verifications._get_age_from_date(child['dob'], product.date) < 3:
                                amount += product.price
                                tickets.append({
                                    'payee': child_id,
                                    'price': product.price,
                                    'product': key
                                })
                                continue
                            
                            # Count of products owned for a trimester
                            count = 5

                            if count > 4:
                                # print ('count > 4')

                                if product.category in [10, 11, 12, 13, 14, 15]:
                                    q = intel.quotient_1
                                    qs = '1'
                                else:
                                    q = intel.quotient_2
                                    qs = '2'

                                # if not q:
                                #     tickets.append({
                                #         'payee': child_id,
                                #         'product': product_id
                                #         'obs': 'Quotient {} non renseigné'.format(qs),
                                #     })
                                #     continue
                                
                                # if q == 1:
                                if q == 2:
                                    price = product.price_q2 # Q2
                                elif q == 3:
                                    price = product.price_q1 # Q1
                                else:
                                    price = product.price  # NE

                                amount += price
                                # print (price)
                                tickets.append({
                                    'payee': child_id,
                                    'price': price,
                                    'product': key
                                })

                            else:
                                amount += product.price
                                tickets.append({
                                    'payee': child_id,
                                    'price': product.price,
                                    'product': key
                                })

            return amount, tickets, tickets_invalid 

    """ admin function ? """
    @staticmethod
    def create_order (data, force_completed=False, order_status=StatusEnum.WAITING, is_admin=False):
        """
        Parameters
        ----------
        data (dict) -> {
            type
            comment
            reference
            caster
            payer     

            cart []
            methods [       ? optional - only on instant paying
                amount
            ]
        }

        Returns
        -------
        dict
            order - order recently created
            status
                201 if there is nothing to pay (credit > amount)
                402 if there is something to pay (credit < amount)
                400 if amount is incorrect and force_completed is True

        Raises
        ------
        BadRequestException
            if cart contains errors
            if there is an active order
            if amount is not correct
            if somewhat error occured
        FormValidationException
            if order data are incorrect
            if method data are incorrect
        """
        # Verify last parent orders
        # Raise an error
        verify_payer_orders(data['payer'])
        
        # Verify products without credit
        # Raise BadRequestException on error
        verify_result = OrderHelper.verify_order({
            'payer': data['payer'],
            'caster': data['caster'],
            'cart': data['cart'],
        }, soft=True)

        if verify_result['tickets_invalid']:
            raise BadRequestException('Création impossible: le panier contient des produits invalides.')
        
        f = OrderForm(data)
        if not f.is_valid():
            # print (f.errors.as_data())
            print (data['type'])
            raise FormValidationException(f.errors)

        # Get client account and credit
        try:
            client = Client.objects.get(pk=f.cleaned_data['payer'])
            credit = client.credit

        except:
            client = None
            credit = 0

        # Prepare methods
        methods = []
        amount_rcvd = 0
        amount_expected = verify_result['amount']

        # Amount expected can be 0 for Q1 parents
        if amount_expected:
            # Deduce credit from amount
            if credit > amount_expected:
                credit = credit - amount_expected
                amount_rcvd = amount_expected

                methods.append(OrderMethod(
                    amount=amount_expected,
                    method=MethodEnum.CREDIT,
                    reference=''
                ))

            else:
                if credit > 0:
                    methods.append(OrderMethod(
                        amount=credit,
                        method=MethodEnum.CREDIT,
                        reference=''
                    ))

                    amount_rcvd = credit
                    credit = 0

        # amount_credit meant credit used
        amount_credited = amount_rcvd 
        # amount_expected -= amount_credited
        
        # Prepare payment method(s) - optional
        # Because of VADS we always have to check methods
        if 'methods' in data:
            _, __ = create_methods(data['methods'], is_admin=is_admin)
            methods += _
            amount_rcvd += __            

        # Compare amounts
        if 'methods' in data or force_completed:
            # Compare amounts if methods - check errors
            if amount_rcvd != amount_expected:
                raise BadRequestException (f'Montant incorrect. Attendu: {amount_expected - amount_credited} €.')

        # Alter stocks
        for item in verify_result['tickets']:
            try:
                product = Product.objects.get(pk=item['product'])
                product.stock_current += 1
                product.save()

            except KeyError as e:
                raise BadRequestException ('Payload invalide. Erreur clé ({}).'.format(str(e)))

            except Product.DoesNotExist:
                raise BadRequestException ('Produit ({}) introuvable.'.format(item['product']))

            except Exception as e:
                raise BadRequestException (f'Une erreur est survenue ({str(e)}).')

        # Order creation
        try:
            order = Order()
            # order.id = Order.objects.latest('id').id + 1
            order.name = NAME
            # order.name = f.cleaned_data['name']
            order.comment = f.cleaned_data['comment']
            order.reference = f.cleaned_data['reference']

            order.type = f.cleaned_data['type']
            order.payer = f.cleaned_data['payer']
            order.caster = f.cleaned_data['caster']

            order.amount = verify_result['amount']
            order.amount_rcvd = amount_rcvd

            order.save()

            # Add status
            if amount_rcvd == amount_expected:
                order._add_status(StatusEnum.COMPLETED)
                ticket_status = StatusEnum.COMPLETED
            else:
                order._add_status(order_status)
                ticket_status = order_status

            # Add methods
            for method in methods:
                # method.id = OrderMethod.objects.latest('id').id + 1
                method.order = order
                method.save()

            # Add tickets
            for t in verify_result['tickets']:
                ticket = Ticket.objects.create(
                    # id = Ticket.objects.latest('id').id + 1,
                    payee = t['payee'],
                    price = t['price'],
                    product = t['product'],

                    order = order
                )

                # Add ticket status
                ticket._add_status(ticket_status)

            if amount_rcvd == amount_expected:
                order.complete()

            order.save()

        except Exception as e:
            raise BadRequestException(f'Une erreur est survenue ({str(e)}).')      
        
        # On success Update credit
        if client and credit:
            # Release 1.4
            client.set_credit(
                credit,
                data['caster'],
                HTE.CREDIT_CONSUMED,
                'Opération système: Achat de prestations.'
            )

        if amount_rcvd != amount_expected:
            return_status = status.HTTP_402_PAYMENT_REQUIRED
        else:
            return_status = status.HTTP_201_CREATED

        return {
            'order': order,
            'status': return_status
        }

    @staticmethod
    def instant_pay_order (data, is_admin=False):
        """
        See OrderHelper.create_order

        NOTE methods are mandatory
        """
        res = OrderHelper.create_order(data, force_completed=True, is_admin=is_admin)

        if res['status'] != status.HTTP_201_CREATED:
            # Cancel order
            res['order'].status.create(
                # id = OrderStatus.objects.latest('id').id + 1,
                status = StatusEnum.CANCELED
            )

            raise BadRequestException('Une erreur est survenue lors de la création du reçu, il sera donc annulé.')

        return res
    
    """ Might be useless in 1.5.4 """
    @staticmethod
    def confirm_order (data):
        """

        """
        if 'methods' in data:
            raise BadRequestException('Aucune méthode de paiement requise.')

        res = OrderHelper.create_order(data)

        return res

    """ admin reservation """
    """ Might be useless in 1.5.4 """
    @staticmethod
    def reserve_order(data):
        res = OrderHelper.create_order(data, order_status=StatusEnum.RESERVED)

        return res
        

    @staticmethod
    def pay_order (order, methods, is_admin=False):
        """
        Return
        ------
        On succes => order
        On failure => Exception

        Exceptions
        ----------
        BadRequestException
        """
        ALLOWED_ORDER_STATUS = [
            StatusEnum.WAITING,
            StatusEnum.RESERVED
        ]

        last_status = order.status.first()
        if last_status.status not in ALLOWED_ORDER_STATUS:
            raise BadRequestException('Impossible de payer le reçu avec le status actuel.')
        
        try:
            ms, amount_rcvd = create_methods(methods, is_admin=is_admin)
        except ForbiddenException as e:
            raise e
        except Exception as e:
            raise BadRequestException('Payload incorrect.')

        amount_expected = order.amount - order.amount_rcvd

        if amount_expected != amount_rcvd:
            raise BadRequestException (f'Montant incorrect. Attendu: {amount_expected} €.')

        for m in ms:
            m.order = order
            m.save()

        order.amount_rcvd += amount_expected
        order._add_status(StatusEnum.COMPLETED)
        for ticket in order.tickets.all():
            ticket._add_status(StatusEnum.COMPLETED)
            
        order.save()

        return order

    @staticmethod
    def ipn_pay_v1(data, is_admin=False):
        """
        data is formated in payment_vads.views.api_vads_ipn
        Parameters
        ----------
        data => dict {
            cart
            payer
            amount
            transaction_id
        }
        """
        # if 'payer' not in data:
        #     raise BadRequestException('Aucun payeur fournie.')

        # if 'cart' not in data:
        #     raise BadRequestException('Aucun produit fournie.')

        # if 'amount' not in data:
        #     raise BadRequestException('Aucun montant de paiement fournie.')
        
        payload = {
            'type': OrderTypeEnum.ONLINE.value,
            'comment': '',
            'reference': '',

            'cart': data['cart'],
            'payer': data['payer'],
            'caster': data['payer'],

            'methods': [{
                'amount': data['amount'],
                'reference': data['transaction_id'],
                'method': MethodEnum.ONLINE_VADS.value
            }]
        }

        res = OrderHelper.create_order(payload, is_admin=is_admin)

        if res['status'] != status.HTTP_201_CREATED:
            res['order'].status.create(
                # id = OrderStatus.objects.latest('id').id + 1,
                status = StatusEnum.CANCELED
            )

            raise BadRequestException('Une erreur est survenue lors de la création du reçu, il sera donc annulé.')

        return res

    @staticmethod
    def ipn_pay_v2(data, is_admin=False):
        """
        data is formated in payment_vads.views.api_vads_ipn
        Parameters
        ----------
        data => dict {
            amount
            order_id
            transaction_id
        }
        """
        # if 'payer' not in data:
        #     raise BadRequestException('Aucun payeur fournie.')

        # if 'cart' not in data:
        #     raise BadRequestException('Aucun produit fournie.')

        # if 'amount' not in data:
        #     raise BadRequestException('Aucun montant de paiement fournie.')
        
        try:
            order = Order.objects.get(pk=data['order_id'])
        except Order.DoesNotExist:
            raise BadRequestException('Reçu introuvable.')

        methods = [{
            'amount': data['amount'],
            'reference': data['transaction_id'],
            'method': MethodEnum.ONLINE_VADS.value
        }]

        order = OrderHelper.pay_order(order, methods, is_admin)
        return order


    @staticmethod
    def cancel_tickets (data, type=HTE.TICKET_CANCELATION.value, order=None):
        """
        Parameters
        ----------
        data => object {
            client => id
            tickets => list of ids - Only in the same order
        }

        Steps
        -----
        Get client data/create if not
        Get sibling
            Store children IDs
        Get order ID from 1st ticket
        Verify tickets
            Get siblings
            Get tickets
            Check payee id
            Increase refound amount
            Set it as CANCELED
        Update client account
        """
        if not data['tickets']:
            return  'Aucun ticket à annuler.'

        # Get sibling
        try:
            sibling = Sibling.objects.get(parent=data['client'])
        except:
            return 'Famille introuvable pour le parent: {}.'.format(data['client'])

        # Gather sibling children ids
        children = [sc.child for sc in sibling.children.all()]

        # Order
        if not order:
            try:
                order = Order.objects.get(tickets__pk=data['tickets'][0])

                if order.payer != data['client']:
                    return 'Ce reçu n\'appartient pas à ce parent.'
            except:
                return 'Reçu introuvable.'

        # print (children)

        # Get tickets
        # And check payee
        amount = 0
        canceled = 0
        cancel_status = []

        # Cache for products
        products = {}

        for ticket_id in data['tickets']:
            try:
                ticket = order.tickets.get(pk=ticket_id)
                
                if ticket.payee in children:

                    # Caching
                    if ticket.product not in products: 
                        product = Product.objects.get(pk=ticket.product)
                        products[ticket.product] = product

                    else:
                        product = products[ticket.product]

                    # Cancelation
                    status = ticket.status.first()

                    # Status - Batch filtering
                    _cancel_list = [
                        StatusEnum.UNSET,
                        StatusEnum.REPORTED,
                    ]

                    _cancel_stock_list = [
                        StatusEnum.WAITING,
                        StatusEnum.RESERVED
                    ]

                    _refund_list = [
                        StatusEnum.COMPLETED
                    ]

                    _already_canceled = [
                        StatusEnum.CANCELED,
                        StatusEnum.REFUNDED
                    ]

                    # print(status.status)

                    if status.status in _cancel_list:
                        ticket._add_status(StatusEnum.CANCELED)
                        cancel_status.append(f'Attention: le ticket ({ticket_id}) ne sera pas crédité.')

                    elif status.status in _cancel_stock_list:
                        ticket._add_status(StatusEnum.CANCELED)
                        cancel_status.append(f'Attention: le ticket ({ticket_id}) ne sera pas crédité.')

                        # Stock
                        product.stock_current -= 1
                        product.save()

                    # COMPLETED
                    elif status.status in _refund_list:
                        amount += ticket.price
                        ticket._add_status(StatusEnum.CANCELED)
                        cancel_status.append(f'Succès: le ticket ({ticket_id}) sera crédité de {ticket.price} €.')

                        # Stock
                        product.stock_current -= 1
                        product.save()

                    elif status.status in _already_canceled:
                        cancel_status.append(f'Attention: le ticket ({ticket_id}) a déjà été annulé, il ne sera pas crédité.')

                    else:
                        cancel_status.append(f'Erreur: status non géré sur le ticket ({ticket_id}), il ne sera pas crédité.')
                    
                    canceled += 1

                else:
                    cancel_status.append(f'Erreur: le ticket ({ticket_id}) de l\'enfant ({ticket.payee}) n\'est pas lié parent.')

            except Ticket.DoesNotExist:
                cancel_status.append(f'Erreur: le ticket ({ticket_id}) n\'appartient pas à ce reçu.')

            except Product.DoesNotExist:
                cancel_status.append(f'Erreur: le produit ({ticket.product}) du ticket ({ticket_id}) n\'existe pas.')

        # 1.5.3
        if amount:
            status = update_credit(
                order.payer,
                {
                    'type': type,
                    'credit': amount,
                    'caster': 0,
                    'comment': 'Opération système'
                }
            )
            if status['status'] == 'Failure':
                cancel_status = [f'Erreur: l\'annulation à échouer avec le message: {status["message"]}.']
                print (status)

        # 1.5.2
        if not order.cancel(amount):
            cancel_status.append(f'Erreur: échec de l\'annulation du reçu.')

        if canceled == len(order.tickets.all()):
            cancel_status.append(f'Information: tous les tickets ont été annulé, ce reçu est annulé.')

        # Update credit
        # Release 1.4
        # ~ moved away

        return cancel_status


    @staticmethod
    def cancel_order (data):
        """
        Parameters
        ----------
        data => object {
            client => id
            order_id => id
        }

        Steps
        -----
        Get order
        Get tickets
        Run cancel_tickets func
        """
        # Order
        try:
            order = Order.objects.get(pk=data['order_id'])
        except:
            return 'Reçu introuvable.'

        tickets = [ticket.id for ticket in order.tickets.all()]

        return OrderHelper.cancel_tickets({
                'client': data['client'],
                'tickets': tickets
            }, 
            type=HTE.ORDER_CANCELATION.value,
            order=order
        )

    @staticmethod
    def _cancel_order (order):
        pass

    # Release 1.5.2
    @staticmethod
    def cancel(order, amount, type):
        pass


