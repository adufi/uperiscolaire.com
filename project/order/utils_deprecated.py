import sys
import copy
import json
import pytz
import requests

from datetime import datetime

from django.db import transaction
from django.utils.timezone import now
from django.http import QueryDict

from rest_framework import status

from .forms import OrderForm, OrderMethodForm
from .models import Order, Ticket, OrderMethod, OrderStatus, TicketStatus, StatusEnum, MethodEnum, OrderTypeEnum, StatusEnum

from params.models import Product
from accounting.models import Client, ClientCreditHistory, HistoryTypeEnum as HTE
from registration.models import Sibling

from users.utils import InternalErrorException, BadRequestException, NotFoundException, UnauthorizedException, ForbiddenException, _localize
from users.exceptions import FormValidationException
# from project.exceptions import FormValidationException

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


class OrderHelper:
    @staticmethod
    def cancel_tickets (data, type=HTE.TICKET_CANCELATION):
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
        try:
            client = Client.objects.get(pk=data['client'])
            # print ('client exist')
        except Client.DoesNotExist:
            # print ('create client')
            client = Client.create(data['client'])

        # Get sibling
        try:
            sibling = Sibling.objects.get(parent=data['client'])
        except:
            return 'Famille introuvable pour le parent: {}.'.format(data['client'])

        # Gather sibling children ids
        children = [sc.child for sc in sibling.children.all()]

        # Order
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

                    # RESERVED
                    if status.status == 1:
                        ticket._add_status(StatusEnum.CANCELED)
                        cancel_status.append(f'Attention: le ticket ({ticket_id}) a été réservé, il ne sera pas crédité.')

                        # Stock
                        product.stock_current -= 1
                        product.save()

                    # COMPLETED
                    elif status.status == 2:
                        amount += ticket.price
                        ticket._add_status(StatusEnum.CANCELED)
                        cancel_status.append(f'Succès: le ticket ({ticket_id}) a bien été crédité de {ticket.price} €.')

                        # Stock
                        product.stock_current -= 1
                        product.save()

                    else:
                        cancel_status.append(f'Attention: le ticket ({ticket_id}) a déjà été annulé, il ne sera pas crédité.')
                    
                    canceled += 1

                else:
                    cancel_status.append(f'Erreur: le ticket ({ticket_id}) de l\'enfant ({ticket.payee}) n\'est pas lié parent.')

            except Ticket.DoesNotExist:
                cancel_status.append(f'Erreur: le ticket ({ticket_id}) n\'appartient pas à ce reçu.')

            except Product.DoesNotExist:
                cancel_status.append(f'Erreur: le produit ({ticket.product}) du ticket ({ticket_id}) n\'existe pas.')

        if canceled == len(order.tickets.all()):
            order._add_status(StatusEnum.CANCELED)
            cancel_status.append(f'Information: tous les tickets ont été annulé, ce reçu est annulé.')

        # Update credit
        # Release 1.4
        client.update_credit(
            amount,
            0,
            type,
            'Opération système'
        )

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
        }, HTE.ORDER_CANCELATION)


    @staticmethod
    def verify_order (data, soft=False):
        """
            PAYLOAD {
                payer: int
                caster: int
                peri: dict
                alsh: dict
            }
        """
        verify_result = OrderHelper.Verifications._verify(data)

        if soft:
            return verify_result

        # If hard
        try:
            client = Client.objects.get(pk=data['payer'])
            credit = client.credit
        
            if credit > verify_result['amount']:
                verify_result['amount'] = 0

            else:
                verify_result['amount'] = verify_result['amount'] - credit
                
        # If client does not exist return normal amount
        except Exception:
            # raise BadRequestException(e)
            pass

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
                raise BadRequestException('Payload invalide. Erreur clé ({})'.format(str(e)))

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
                raise BadRequestException(e)

            verify_result = {}
            verify_result['amount'] = amount
            verify_result['tickets'] = tickets
            verify_result['tickets_invalid'] = tickets_invalid

            if not verify_result['tickets']:
                raise BadRequestException('Le panier contient des erreurs.')

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
                return 'Aucune année scolaire active.'

            except Sibling.DoesNotExist:
                return 'Aucune parenté trouvé pour ce payeur ({})'.format(payer_id)

            except SiblingIntels.DoesNotExist:
                return 'Aucun dossier familiale trouvé pour ce payeur ({})'.format(payer_id)

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
                    raise Exception('Payload invalide avec l\'erreur ({}) '.format(str(e)))

                # Check there are children
                if not children_ids:
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
                                'obs': 'Produit déjà possédé.'
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
                    amount += TARIFS_PERI[index - 1]

                    # print ('index: ', index)
                    # print ('amount: ', amount)

                    for child_id in item['children']:
                        price = TARIFS_PERI[index - 1] / count
                        # price = round(TARIFS_PERI[index - 1] / count)
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

                    print ('# Stock')
                    print (key)
                    print (lenc)
                    print (left)

                    if lenc > left and product.stock_max != 0:
                        tickets_invalid.append({
                            'payee': -1,
                            'product': key,
                            'obs': 'Le produit ne dispose pas assez de stock.' # ({} restant(s)).'.format(left)
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


    """ admin function """
    @staticmethod
    def create_order (data):
        """
        Parameters
        ----------
        data {
            type
            name
            comment
            reference
            caster
            payer
            amount    

            status      default=WAITING        

            cart []
            methods []
        }
        
        Returns
        -------
        dict
            order - order recently created
            status
                201 if there is nothing to pay (credit > amount)
                402 if there is something to pay (credit < amount)
        """

        # Verify products
        # Raise BadRequestException on error
        verify_result = OrderHelper.verify_order({
                'payer': data['payer'],
                'caster': data['caster'],
                'cart': data['cart'],
            }, True)

        ALLOWED_ORDER_STATUS = [
            StatusEnum.COMPLETED, 
            StatusEnum.CANCELED,
            StatusEnum.REFUNDED
        ]

        # Verify last parent order
        # if order is not complete
        # and is still valid
        # raise an error
        last_order = Order.objects.filter(payer=data['payer']).last()
        if last_order:

            # Status check
            last_status = last_order.status.first()
            if last_status.status not in ALLOWED_ORDER_STATUS:

                # Expiration check
                if not last_order.has_expired():
                    raise BadRequestException('Une commande est déjà en cours pour ce parent.')
        
        f = OrderForm(data)
        if not f.is_valid():
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
        amount_total = 0

        # Deduce credit from amount
        if credit > verify_result['amount']:
            credit = credit - verify_result['amount']
            amount_expected = 0

            methods.append(OrderMethod(
                amount=verify_result['amount'],
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

                amount_expected = verify_result['amount'] - credit
                credit = 0

            else:
                amount_expected = verify_result['amount']
                
        # Prepare payment method(s)
        for m in data['methods']:
            mf = OrderMethodForm(m)
            if not mf.is_valid():
                raise FormValidationException(mf.errors)

            amount_total += float(m['amount'])
            methods.append(OrderMethod(
                amount=m['amount'],
                method=m['method'],
                reference=m['reference']
            ))

        # Compare amounts - check errors
        if amount_total != amount_expected:
            raise BadRequestException (f'Montant incorrect. Attendu: {amount_expected} €.')

        # Alter stocks
        for item in data['cart']:
            try:
                product = Product.objects.get(pk=item['product'])
                count = len(item['children'])

                # Check max count
                if product.stock_max != 0:
                    left = product.stock_max - product.stock_current
                    if count > left:
                        raise BadRequestException ('Le produit ({}) ne contient pas suffisamment de place.'.format(item['product']))

                product.stock_current += count
                product.save()

            except KeyError as e:
                raise BadRequestException ('Payload invalide. Erreur clé ({}).'.format(str(e)))

            except Product.DoesNotExist:
                raise BadRequestException ('Un produit sélectionné est invalide ({}).'.format(item['product']))

            except Exception as e:
                raise BadRequestException (f'Une erreur est survenue ({str(e)}).')

        # Order creation
        try:
            order = Order()
            order.id = Order.objects.latest('id').id + 1
            order.name = NAME
            # order.name = f.cleaned_data['name']
            order.comment = f.cleaned_data['comment']
            order.reference = f.cleaned_data['reference']

            order.type = f.cleaned_data['type']
            order.payer = f.cleaned_data['payer']
            order.caster = f.cleaned_data['caster']

            order.amount = amount_expected

            order.save()

            # Add status
            order_status = OrderStatus()
            order_status.id = OrderStatus.objects.latest('id').id + 1
            order_status.status = StatusEnum.WAITING
            order.status.add(order_status)

            if amount_expected == 0:
                order_status = OrderStatus()
                order_status.id = OrderStatus.objects.latest('id').id + 1
                order_status.status = StatusEnum.COMPLETED
                order.status.add(order_status)


            # Add methods
            for method in methods:
                method.id = OrderMethod.objects.latest('id').id + 1
                method.order = order
                order.methods.add(method)

            # Add tickets
            for t in verify_result['tickets']:
                ticket = Ticket()
                ticket.id = Ticket.objects.latest('id').id + 1
                ticket.payee = t['payee']
                ticket.price = t['price']
                ticket.product = t['product']

                ticket.order = order
                order.tickets.add(ticket)

                # Add ticket status
                ticket_status = TicketStatus()
                ticket_status.id = TicketStatus.objects.latest('id').id + 1
                ticket_status.status = StatusEnum.WAITING
                ticket.status.add(ticket_status)

                if amount_expected == 0:
                    ticket_status = TicketStatus()
                    ticket_status.id = TicketStatus.objects.latest('id').id + 1
                    ticket_status.status = StatusEnum.COMPLETED
                    ticket.status.add(ticket_status)

        except Exception as e:
            raise BadRequestException(f'Une erreur est survenue ({str(e)}).')      
        
        # On success Update credit
        if client:
            # Release 1.4
            client.set_credit(
                credit,
                data['caster'],
                HTE.CREDIT_CONSUMED,
                'Opération système: Achat de prestations.'
            )

        if amount_expected == 0:
            return_status = status.HTTP_402_PAYMENT_REQUIRED
        else:
            return_status = status.HTTP_201_CREATED

        return {
            'order': order,
            'status': return_status
        }


    """ admin function """
    @staticmethod
    def reserve(data):
        pay_result = {
            'status': 'Failure'
        }

        verify_payload = {
            'payer': data['payer'],
            'caster': data['caster'],
            'peri': data['peri'],
            'alsh': data['alsh'],
        }

        # Verify products
        verify_result = OrderHelper.verify(verify_payload, True)

        # On verification failure
        if verify_result['status'] == 'Failure':
            pay_result['message'] = verify_result['message']
            return pay_result

        # Every products should be valid
        if 'tickets_invalid' in verify_result and verify_result['tickets_invalid']:
            # print (verify_result)
            pay_result['message'] = 'Cart contains invalid products.'
            return pay_result

        # Prepare creation
        create_payload = {
            'name':         NAME,
            'comment':      data['comment'],
            'type':         data['type'],
            'reference':    data['reference'],
            'payer':        data['payer'],
            'caster':       data['caster'],

            'status': {
                'status': StatusEnum.RESERVED
            },

            'methods': [],

            'amount': verify_result['amount'],
            'tickets': verify_result['tickets']
        }

        # Create order
        order = OrderHelper._create(create_payload)

        if type(order) is str:
            pay_result['message'] = 'Failed to create an order with error ({}).'.format(order)
            return pay_result

        pay_result['status'] = 'Success'
        pay_result['order'] = {
            'id': order.id
        }

        return pay_result




    """ Code below is to be reviewed """


    """ Not used anymore - see ParamsHelper.Stock """
    class Stock:

        @staticmethod
        def has_stock(product_id, mod=1):
            """
            Parameters
            ----------
            product_id => ...
            mod => amount of iteration for a product

            Returns
            -------
            Boolean
            """
            try:
                product = Product.objects.get(pk=product_id)
                order_stock = OrderStock.objects.get(product=product_id)
                if product.stock == 0:
                    return True
                if (order_stock.count + mod) <= product.stock:
                    return True
                return False
            except Product.DoesNotExist:
                return False
            except OrderStock.DoesNotExist:
                return True

        """ Increase count for a stock/Create if not exist """
        @staticmethod
        def inc(product_id):
            """
            No product verification
            """
            try:
                order_stock = OrderStock.objects.get(product=product_id)
                order_stock.count += 1
                order_stock.save()
            except OrderStock.DoesNotExist:
                order_stock = OrderStock.objects.create(
                    id=product_id,
                    product=product_id,
                    count=1
                )

        """ Decrease count for a stock """
        @staticmethod
        def dec(product_id):
            """
            No product verification
            """
            try:
                order_stock = OrderStock.objects.get(product=product_id)
                if order_stock.count > 0:
                    order_stock.count -= 1
                    order_stock.save()
            except OrderStock.DoesNotExist:
                pass

    class Ticket:

        @staticmethod
        def read_from_child(child_id):
            tickets = Ticket.objects.filter(payee=child_id)
            return tickets


    @staticmethod
    def get_client_data(id):
        try:
            client = Client.objects.get(pk=id)
            return {
                'user': client.user,
                'credit': {
                    'amount': client.credit.amount,
                    'date_created': client.credit.date_created.__str__(),
                    'date_last_mod': client.credit.date_last_mod.__str__()
                }
            }
        except:
            return {} 

    @staticmethod
    def get_order_by_id(id):
        try:
            order = Order.objects.get(pk=id)
        except Order.DoesNotExist:
            return False

        return OrderSerializer(order).data

    @staticmethod
    def get_order_by_id_details(data):
        response = data

        # Get caster
        try:
            caster = User.objects.get(pk=data['caster'])
        except User.DoesNotExist:
            response['caster'] = {
                'id': data['caster']
            }

        # Get payer
        try:
            _payer = User.objects.get(pk=data['payer'])
            payer = UserSerializer(_payer).data
        except User.DoesNotExist:
            response['payer'] = payer


        return OrderSerializer(order).data
    
    @staticmethod
    def report(data):
        """
        Parameters
        ----------
        data => object {
            client => id
            tickets => list of ids
        }

        Steps
        -----
        Get client data/Create if not
        Verify tickets
            Get siblings
            Get tickets
            Check payee id
            Increase refound amount
            Set it as REPORTED
        Update client account
        """
        try:
            client = Client.objects.get(pk=data['client'])
            # print ('client exist')
        except Client.DoesNotExist:
            # print ('create client')
            client = Client.objects.create(
                id=data['client'],
                user=data['client'],
            )
            client.credit = ClientCredit.objects.create(client=client)

        # Get sibling
        try:
            sibling = Sibling.objects.get(parent=data['client'])
        except:
            return 'Failed to get sibling for parent: {}.'.format(data['client'])

        # Gather sibling children ids
        children = []
        for child in sibling.children.all():
            children.append(child.child.id)

        # print (children)

        # Get tickets
        # And check payee
        amount = 0
        # tickets = []

        for ticket_id in data['tickets']:
            ticket = Ticket.objects.filter(pk=ticket_id).first()
            if ticket:
                if ticket.payee in children:
                    # tickets.append(ticket)
                    amount += ticket.price
                    # print (amount)
                    ticket.report()

        client.credit.update(amount)
        return client

    @staticmethod
    def pay(data):
        # print (data)

        pay_result = {
            'status': 'Failure'
        }

        verify_payload = {
            'payer': data['payer'],
            'caster': data['caster'],
            'cart': data['cart'],
            # 'alsh': data['alsh'],
            # 'peri': data['peri'],
        }

        # Verify products
        print ('VERIFY')
        verify_result = OrderHelper.verify_order(verify_payload, True)

        print ('END VERIFY')
        print (verify_result['amount'])

        # On verification failure
        if verify_result['status'] == 'Failure':
            pay_result['message'] = verify_result['message']
            return pay_result

        # Every products should be valid
        if 'tickets_invalid' in verify_result and verify_result['tickets_invalid']:
            # print (verify_result)
            pay_result['message'] = 'Le panier contient des produits invalides.'
            return pay_result

        # Get client account and credit
        try:
            client = AClient.objects.get(pk=data['payer'])
            credit = client.credit
        except:
            client = None
            credit = 0

        # Prepare methods
        methods = []
        amount_total = 0

        # print (verify_result['amount'])
        # print (credit)

        # Deduce credit from amount
        if credit > verify_result['amount']:
            credit = credit - verify_result['amount']
            amount_expected = 0

            methods.append({
                'amount': verify_result['amount'],
                'method': MethodEnum.CREDIT,
                'reference': ''
            })

        else:
            if credit > 0:
                methods.append({
                    'amount': credit,
                    'method': MethodEnum.CREDIT,
                    'reference': ''
                })

                amount_expected = verify_result['amount'] - credit
                credit = 0

            else:
                amount_expected = verify_result['amount']
                
        # Create payment method(s)

        for m in data['methods']:
            if not m['amount']:
                continue

            amount_total += float(m['amount'])
            methods.append({
                'amount': m['amount'],
                'method': m['method'],
                'reference': m['reference']
            })

        # Check amounts
        if amount_total != amount_expected:
            pay_result['message'] = f'Montant incorrect. Attendu: {amount_expected} €.'
            return pay_result
        
        # Alter stocks
        for item in data['cart']:
            try:
                product = Product.objects.get(pk=item['product'])
                count = len(item['children'])

                # Check max count
                if product.stock_max != 0:
                    left = product.stock_max - product.stock_current
                    if count > left:
                        pay_result['message'] = 'Le produit ({}) ne contient pas suffisamment de place.'.format(item['product'])
                        return pay_result

                product.stock_current += count
                product.save()

            except KeyError as e:
                pay_result['message'] = 'Payload invalide. Erreur sur la clé ({}).'.format(str(e))
                return pay_result

            except Product.DoesNotExist:
                pay_result['message'] = 'Le produit ({}) n\'existe pas.'.format(item['product'])
                return pay_result

            except Exception as e:
                pay_result['message'] = 'Une erreur est survenue ({}).'.format(str(e.args[0]))
                return pay_result

        # Prepare creation
        create_payload = {
            'name':         NAME,
            'comment':      data['comment'],
            'type':         data['type'],
            'reference':    data['reference'],
            'payer':        data['payer'],
            'caster':       data['caster'],

            'status': {
                'status': StatusEnum.COMPLETED
            },
            
            'methods': methods,

            'amount': amount_expected,
            'tickets': verify_result['tickets']
        }

        # Create order
        order = OrderHelper._create(create_payload)

        if type(order) is str:
            pay_result['message'] = 'Echèc lors de la création du ticket.'
            return pay_result

        # On success Update credit
        if client:
            # Release 1.4
            client.set_credit(
                credit,
                data['caster'],
                HTE.CREDIT_CONSUMED,
                'Opération système: Achat de prestations.'
            )
        
        pay_result['status'] = 'Success'
        pay_result['order'] = {
            'id': order.id
        }

        return pay_result

    """
    NOTE
        - It should be only on 1 status per order/tickets - If there is more maybe create another functions with arrays

    PAYLOAD
        id
        name
        comment
        reference
        order_type
        date
        amount
        payer
        caster
        methods []      - optional
            id
            amount
            method
            reference
        status
            id
            date
            status
        tickets []
            status - optional but must provide order status
                id
                date
                status
    """
    @staticmethod
    @transaction.atomic
    def _create(data):
        sid = transaction.savepoint()
        try:
            if not 'id' in data:
                id = Order.objects.latest('id').id + 1
            else:
                id = data['id']

            if not 'date' in data:
                date = _localize(datetime.now())
            else:
                date = _localize(data['date'])

            o = Order(
                id=id,
                name=data['name'],
                comment=data['comment'],
                type=data['type'],
                reference=data['reference'],
                date=date,
                caster=data['caster'],
                payer=data['payer'],
                amount=data['amount']
            ) 

            o.save()

            # OrderStatus
            if data['status']:
                status = data['status']
            else:
                status = { 'status': StatusEnum.UNSET }

            status_id = status['id'] if 'id' in status else OrderStatus.objects.latest('id').id + 1

            status_date = _localize(status['date']) if 'date' in status else date
            
            OrderStatus.objects.create(
                id=status_id,
                date=status_date,
                status=status['status'],
                order=o
            )

            # Methods
            if data['methods']:
                for ms in data['methods']:

                    if not 'id' in ms:
                        method_id = OrderMethod.objects.latest('id').id + 1
                    else:
                        method_id = ms['id']
                        
                    OrderMethod.objects.create(
                        id=method_id,
                        amount=ms['amount'],
                        method=ms['method'],
                        reference=ms['reference'],
                        order=o
                    )

            # Tickets
            for _ticket in data['tickets']:

                ticket_id = _ticket['id'] if 'id' in _ticket else Ticket.objects.latest('id').id + 1
                
                ticket = Ticket.objects.create(
                    id=ticket_id,
                    payee=_ticket['payee'],
                    price=_ticket['price'],
                    product=_ticket['product'],
                    order=o
                )

                if not 'status' in _ticket:
                    ts = {
                        'id': TicketStatus.objects.latest('id').id + 1,
                        'date': date,
                        'status': status['status']
                    }
                    
                else:
                    ts = _ticket['status']

                # Set it to COMPLETE
                TicketStatus.objects.create(
                    id=ts['id'],
                    date=ts['date'],
                    status=ts['status'],
                    ticket=ticket
                )

                # Alter stocks
                # ParamsHelper.Stock.inc(_ticket['product'])

            transaction.savepoint_commit(sid)
            return o
        except Exception as e:
            transaction.savepoint_rollback(sid)
            return 'Invalid payload with error: ' + str(e)

        transaction.savepoint_rollback(sid)
        return 'End of function.'



"""
Ensure data is in the correct format
"""
def get_parsed_data(data):
    if not data:
        return False
    if type(data) is QueryDict:
        for x in data:
            return json.loads(x)
    return data


"""
check_authorizations(request, []) => basic auth
check_authorizations(request, ['admin', 'is_superuser'])
"""
def check_authorizations(headers, roles):
    if 'Authorization' in headers:
        try:
            token = headers.get('Authorization').split(' ')[1]
            r = requests.get(
                'http://127.0.0.1:8000/auth/status/',
                # 'http://localhost:8000/ap/auth/status/',
                headers={'Authorization': f'Bearer {token}'}
            )
            if r.status_code != 200:
                return 'Failed to get status'

            if not roles:
                return True

            user = r.json()['user']

            if not hasattr(user, 'roles') and not user['roles']:
                return 'User has not roles'

            for role in user['roles']:
                print(role['slug'])
                if role['slug'] in roles:
                    return True

            return 'Function ended'
        except IndexError:
            return 'Function threw IndexError'
    else:
        return 'Headers doesn\'t have bearer'



"""
Convert a str date into a date according to format %Y-%m-%d %H:%M:%S
"""
def localize(strdate):
    date = datetime.strptime(strdate, '%Y-%m-%d %H:%M:%S')
    return pytz.utc.localize(date)


"""
Order (Migration) {
    id
    name
    comment
    order_type
    reference
    date
    caster
    payer
    amount

    methods [{
        id
        amount
        method
        reference
    }]

    tickets [{
        id
        payee
        price
        product
    }]


    ###############"
    status [{
        date
        status
    }]
}
"""
@transaction.atomic
def create_order_migration(data):
    sid = transaction.savepoint()
    try:
        # Create user
        if not 'id' in data:
            return 'No ID provided.'

        o = Order(
            id=data['id'],
            name=data['name'],
            comment=data['comment'],
            order_type=data['order_type'],
            reference=data['reference'],
            date=localize(data['date']),
            caster=data['caster'],
            payer=data['payer'],
            amount=data['amount']
        )

        o.save()

        if data['methods']:
            for ms in data['methods']:
                OrderMethod.objects.create(
                    id=ms['id'],
                    amount=ms['amount'],
                    method=ms['method'],
                    reference=ms['reference'],
                    order=o
                )

        # Suspend status 
        # for os in data['order_status']:
        #     OrderStatus.objects.create(
        #         date=localize(os['date']) if 'date' in os else now,
        #         status=os['status'],
        #         order=o
        #     )
        # ...
        # Set it to COMPLETE
        OrderStatus.objects.create(
            date=localize(data['date']),
            status=StatusEnum.COMPLETED,
            order=o
        )


        for ts in data['tickets']:
            ticket = Ticket.objects.create(
                id=ts['id'],
                payee=ts['payee'],
                price=ts['price'],
                product=ts['product'],
                peri_order=o
            )

            # Suspend status
            # for tss in ts['ticket_status']:
            #     TicketStatus.objects.create(
            #         date=localize(tss['date']) if 'date' in tss else now,
            #         status=tss['status'],
            #         ticket=ticket
            #     )
            # ...
            # Set it to COMPLETE
            TicketStatus.objects.create(
                date=localize(data['date']),
                status=StatusEnum.COMPLETED,
                ticket=ticket
            )

        transaction.savepoint_commit(sid)
        return o
    except Exception as e:
        transaction.savepoint_rollback(sid)
        return 'Invalid payload with error: ' + str(e)

    transaction.savepoint_rollback(sid)
    return 'End of function.'


"""
Order {
    name
    comment
    order_type
    caster
    payer
    amount

    methods [{
        method
        reference
        amount
    }]
    
    tickets [{
        payee
        product
        price
    }]

TODO
    add reference
}
"""
@transaction.atomic
def create_order(data):
    sid = transaction.savepoint()
    try:
        o = Order.objects.create(
            name=data['name'],
            comment=data['comment'],
            order_type=data['order_type'],
            caster=data['caster'],
            payer=data['payer'],
            amount=data['amount']
        )

        # Create PENDING status
        OrderStatus.objects.create(
            status=StatusEnum.PENDING,
            order=o
        )

        for ts in data['tickets']:
            ticket = Ticket.objects.create(
                payee=ts['payee'],
                price=ts['price'],
                product=ts['product'],
                peri_order=o
            )

            TicketStatus.objects.create(
                status=StatusEnum.PENDING,
                ticket=ticket
            )

        transaction.savepoint_commit(sid)
        return o
    except Exception as e:
        transaction.savepoint_rollback(sid)
        return 'Invalid payload with error: ' + str(e)

    transaction.savepoint_rollback(sid)
    return 'End of function.'


"""
Order {
    name
    comment
    order_type
    caster
    payer
    amount

    tickets [{
        payee
        product
        price
    }]

TODO
    add reference
}
"""
@transaction.atomic
def create_order_(data):
    sid = transaction.savepoint()
    try:
        latest_id = Order.objects.latest('id').id + 1

        o = Order.objects.create(
            id=latest_id,
            name=data['name'],
            comment=data['comment'],
            reference=data['reference'],
            order_type=data['order_type'],
            caster=data['caster'],
            payer=data['payer'],
            amount=data['amount']
        )
        print('*')

        # Create PENDING status
        OrderStatus.objects.create(
            status=StatusEnum.COMPLETED,
            order=o
        )
        print('**')

        latest_method_id = OrderMethod.objects.latest('id').id

        for method in data['methods']:
            latest_method_id += 1

            OrderMethod.objects.create(
                id=latest_method_id,
                method=method['method'],
                amount=method['amount'],
                reference=method['reference'],
                order=o
            )
        print('***')

        latest_ticket_id = Ticket.objects.latest('id').id

        for ts in data['tickets']:
            print (ts)
            
            latest_ticket_id += 1
            ticket = Ticket.objects.create(
                id=latest_ticket_id,
                payee=ts['payee'],
                price=ts['price'],
                product=ts['product'],
                peri_order=o
            )
            print('****')

            TicketStatus.objects.create(
                status=StatusEnum.COMPLETED,
                ticket=ticket
            )
            print('*****')

        transaction.savepoint_commit(sid)
        print('******')
        return o
    except Exception as e:
        transaction.savepoint_rollback(sid)
        return 'Invalid payload with error: ' + str(e)

    transaction.savepoint_rollback(sid)
    return 'End of function.'


@transaction.atomic
def confirm_order(id, methods):
    sid = transaction.savepoint()
    try:
        order = Order.objects.get(id=id)

        for method in methods:
            OrderMethod.objects.create(
                method=method['method'],
                amount=method['amount'],
                reference=method['reference'],
                order=order
            )

        OrderStatus.objects.create(
            status=StatusEnum.COMPLETED,
            order=order
        )

        for ticket in order.tickets.all():
            TicketStatus.objects.create(
                status=StatusEnum.COMPLETED,
                ticket=ticket
            )

        transaction.savepoint_commit(sid)
        return order

    except Order.DoesNotExist:
        transaction.savepoint_rollback(sid)
        return 'Order does not exist.'

    except Exception as e:
        transaction.savepoint_rollback(sid)
        return 'An exception occured during confirmation process with error: ' + str(e)

    return 'End of function.'


"""
    Useless - Age checked with classroom
"""
def get_age(date_str):
    today = datetime.now()
    birthDate = datetime.strptime(date_str, '%Y-%m-%d')

    age = today.year - birthDate.year
    m = today.month - birthDate.month

    if m < 0 or (m == 0 and today.day < birthDate.day):
        age -= 1

    return age


"""

"""
def has_bought(child, product):
    ts = Ticket.objects.filter(
        payee=child,
        product=product
    ).all()

    for t in ts:
        for status in t.status.all():
            if status.status == StatusEnum.COMPLETED:
                return True
    return False


"""
Verify product validity
Incoming
    caster
    payer
    comment
    peri [{
        'product': int,
        'children': list
    }]
    alsh [{
        'child': int,
        'products': list
    }]

Outcoming
    caster
    payer
    amount
    comment
    tickets
    tickets_invalid


TODO
    verify caster, parent, children
"""
def verify_order(data):
    verify_result = {
        'status': 'Failure',
    }

    try:
        if type(data) is str:
            data = json.loads(data)

        # Get products
        products_response = requests.get(
            'http://localhost:8000/v1/params/details')

        if products_response.status_code != 200:
            verify_result['message'] = 'Failed to get response for products'
            return verify_result

        products = products_response.json()['school_year']['product']

        caster = None
        parent = None

        if data['caster'] != data['payer']:
            # Check caster
            # ...
            caster_response = requests.get(
                f'http://localhost:8000/users/{data["caster"]}',
                headers={'Authorization': f'Bearer {ADMIN_TOKEN}'}
            )

            if caster_response.status_code != 200:
                verify_result['message'] = 'Failed to get response for caster.'
                return verify_result

            caster = caster_response.json()['user']
            roles = ['admin', 'ap_admin', 'is_superuser']
            found = False
            for role in caster['roles']:
                if role['slug'] in roles:
                    found = True
                    break

            if not found:
                verify_result['message'] = 'Not a valid caster.'
                return verify_result

        else:
            # Check parent
            # ...
            parent_response = requests.get(
                f'http://localhost:8000/users/{data["payer"]}',
                headers={'Authorization': f'Bearer {ADMIN_TOKEN}'}
            )

            if parent_response.status_code != 200:
                verify_result['message'] = 'Failed to get response for parent'
                return verify_result

            parent = parent_response.json()['user']
            roles = ['parent']
            found = False
            for role in parent['roles']:
                if role['slug'] in roles:
                    found = True
                    break

            if not found:
                verify_result['message'] = 'Not a valid parent.'
                return verify_result


        # Get siblings
        siblings_response = requests.get(
            f'http://localhost:8000/v1/siblings/parent/{data["payer"]}',
            headers={'Authorization': f'Bearer {ADMIN_TOKEN}'}
        )

        if siblings_response.status_code != 200:
            verify_result['message'] = 'Failed to get response for siblings'
            return verify_result

        siblings = []
        for s in siblings_response.json()['siblings']['siblings']:
            siblings.append(s['child'])

        if not siblings:
            verify_result['message'] = 'Failed to get siblings'
            return verify_result


        # Check children
        # ...
        # check children in sub verification


        # Verify order output
        if verify_result['status'] == 'Failed':
            print('Failed')

        # print (f'data cart: {data["cart"]}')
        # print(type(data))
        # cart = copy.deepcopy(data['cart'])
        # if not cart:
        #     verify_result['message'] = 'Failed to get cart'
        #     return verify_result

        print('4')

        amount = 0

        tickets = []
        tickets_invalid = []


        # Check peri
        print('3')
        amount, tickets, tickets_invalid = verify_order_peri(siblings, products, data['peri'])


        # Check alsh
        print('2')
        _amount, _tickets, _tickets_invalid = verify_order_alsh(siblings, products, data['alsh'])


        print('1')
        verify_result['status'] = 'Success'

        verify_result['amount'] = amount + _amount
        verify_result['tickets'] = tickets + _tickets
        verify_result['tickets_invalid'] = tickets_invalid + _tickets_invalid

        return verify_result

    except KeyError as e:
        print('Wrong payload: ' + str(e))
        verify_result['message'] = 'Wrong payload: ' + str(e)

    except Exception as e:
        # print(verify_result['message'])
        print('An error occured ', sys.exc_info()[0])
        print('An error occured ', str(e))
        verify_result['message'] = 'An error occured: %1'.format(sys.exc_info()[0])

    return verify_result


"""
peri [{
    'product': int,
    'children': list
}]

peri [{
    'product': 12,
    'children': [50, 51, 52]
}]
"""
def verify_order_peri(siblings, products, peri):
    amount = 0

    tickets = []
    tickets_invalid = []

    print('a')
    for month in peri:

        # Check there are children
        if not month['children']:
            continue

        # Product lookup
        # product can be non-existant
        # product can be non-peri
        # product was found
        print('b')
        product = None
        for p in products:
            if month['product'] == p['id']:
                # Check product is a valid peri product
                if p['category'] != 1:
                    break
                product = p

        # Product not found
        if not product:
            print('c')
            for child in month['children']:
                tickets_invalid.append({
                    'payee': child,
                    'product': month['product'],
                    'obs': 'Product not found'
                })
            continue

        children_count = 0

        # Loop through children
        # Count eligible children
        print('d')
        for child in month['children']:
            # Check child is in siblings
            if not child in siblings:
                tickets_invalid.append({
                    'payee': child,
                    'product': product['id'],
                    'obs': 'Child is not bind to parent.'
                })
                continue

            # Check child never bought product
            # If bought goto next child
            if has_bought(child, product['id']):
                tickets_invalid.append({
                    'payee': child,
                    'product': product['id'],
                    'obs': 'Product already bought.'
                })
                continue

            tickets.append({
                'payee': child,
                'product': product['id']
            })
            children_count += 1

        # Calculate product price
        print('e')
        if children_count:
            # Set price
            n = 4 if children_count > 4 else children_count
            amount += TARIFS_PERI[n - 1]
            price = TARIFS_PERI[n - 1] / children_count

            print('f')
            # Update tickets
            for i in range(len(tickets)):
                if tickets[i]['product'] == product['id']:
                    tickets[i]['price'] = price

        print('g')

    return amount, tickets, tickets_invalid


"""
alsh [{
    'child': int,
    'products': list
}]

alsh [{
    'child': 12,
    'products': [78, 79, 80]
}]
"""
def verify_order_alsh(siblings, products, alsh):
    # NOTE
    # Products should be ordered by trimesters

    amount = 0

    tickets = []
    tickets_invalid = []

    for row in alsh:
        child = row['child']
        pids = row['products']

        # Check child is in siblings
        if child not in siblings:
            for pid in pids:
                tickets_invalid.append({
                    'payee': child,
                    'product': pid,
                    'obs': 'Child is not bind to parent.'
                })
            continue

        # Check child
        # age
        child_response = requests.get(
            f'http://localhost:8000/users/{child}',
            headers={'Authorization': f'Bearer {ADMIN_TOKEN}'}
        )

        if child_response.status_code != 200:
            for pid in pids:
                tickets_invalid.append({
                    'payee': child,
                    'product': pid,
                    'obs': 'Child not found.'
                })
            continue

        _age = child_response.json()['user']['dob'];
        age = get_age(_age)
        print (_age)

        # classroom
        # quotient
        child_response = requests.get(
            f'http://localhost:8000/v1/records/child/{child}',
            headers={'Authorization': f'Bearer {ADMIN_TOKEN}'}
        )

        if child_response.status_code != 200:
            for pid in pids:
                tickets_invalid.append({
                    'payee': child,
                    'product': pid,
                    'obs': 'Record not found.'
                })
            continue
        
        record = child_response.json()['record']
        print (record['classroom'])


        # Can't check for records
        # ...
        # child = child_response.json()['user']
        # if 'child' not in child['roles']:
        #     verify_result['message'] = 'Not a valid child records.'
        #     return verify_result
            
        age_range = 2
        if record['classroom'] >= 1 and record['classroom'] <= 4:
            age_range = 1

        print('*')
        for pid in pids:
            # Check child orders
            if has_bought(child, pid):
                tickets_invalid.append({
                    'payee': child,
                    'product': pid,
                    'obs': 'Product already bought.'
                })
                continue

            # Check stock
            # ...

            print('**')
            product = None
            # Lookup product
            for p in products:
                if p['id'] == pid:
                    if p['category'] == 0 or p['category'] == 1:
                        break
                    product = p
            

            # Check child age for product
            print('***')
            if not product:
                tickets_invalid.append({
                    'payee': child,
                    'product': pid,
                    'obs': 'Not a valid ALSH product.'                
                })
                continue

    
            print('****')
            if age_range != product['subcategory']:
                tickets_invalid.append({
                    'payee': child,
                    'product': pid,
                    'obs': 'Wrong product for the age.'
                })
                continue

            # Maths
            key = 'price'
            key = 'price_q2' if record['caf']['quotient_q2'] == 2 else key
            key = 'price_q1' if record['caf']['quotient_q2'] == 3 else key

            # Check age
            if age < 2:
                # Check product date
                d1 = datetime.strptime(product['date'], '%Y-%m-%d')
                d2 = datetime.strptime(_age, '%Y-%m-%d')

                if d1 > d2:
                    key = 'price'

            price = product[key]
            amount += price
            tickets.append({
                'payee': child,
                'product': pid,
                'price': price
            })

        # Order products
        # for p in alsh['products']:

        #     for product in products:
        #         if product['id'] == p:
        #             pass
                    # Check product stock

                    # Check child orders

    return amount, tickets, tickets_invalid
