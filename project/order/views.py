import json
import requests

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .utils import OrderHelper, NAME, cancel_order
from .models import Order, Ticket, OrderMethod, OrderStatus, TicketStatus, StatusEnum, OrderTypeEnum, MethodEnum
from .serializers import OrderSerializer, TicketSerializer

from users.utils import paginate, get_parsed_data
from users.decorators import login_required

from users.exceptions import BadRequestException, ForbiddenException, exception_to_response

from registration.models import Sibling

from params.models import Product, SchoolYear
from params.serializers import ProductSerializer

# Create your views here.

def order_demo(request):
    sy = SchoolYear.objects.get(is_active=True)
    products = sy.products.all()
    return render(request, 'intern/Order/Demo.html', {
        'products': ProductSerializer(products, many=True).data
    })


def order_print(request, pk):
    sy = SchoolYear.objects.get(is_active=True)
    products = sy.products.all()
    return render(request, 'intern/Order/Print.html', {
        'products': ProductSerializer(products, many=True).data
    })


@api_view(['POST'])
def api_order_ipn (request):
    raise NotImplementedError
    print (request.data)
    print (request.POST)
    return JsonResponse({'status': 'Success'}, status=status.HTTP_200_OK)

""" List orders - Filter by parameters """
@api_view(['GET'])
@login_required(['is_superuser', 'admin', 'parent'])
def api_orders(request, pk=0):
    response_object = {
        'status': 'Failure'
    }

    try:
        is_admin = False
        sibling = None
        
        if 'admin' in request.META['check']['role']:
            is_admin = True

        if 'parent' in request.META['check']['role']:
            sibling = Sibling.objects.get(parent=request.META['check']['id'])

        pk = request.GET.get('pk', 0) if not pk else pk
        if pk:
            print (pk)
            order = Order.objects.get(pk=pk)
            response_object['order'] = OrderSerializer(order).data

        else:
            all = Order.objects.all().order_by('-date')
            filtered = all

            to_list = lambda s: s.split(',')

            payer = request.GET.get('payer', 0)
            caster = request.GET.get('caster', 0)
            payer_in = request.GET.get('payer_in', 0)
            caster_in = request.GET.get('caster_in', 0)

            # Parent security check
            if not is_admin:
                payer = request.META['check']['id']
                payer_in = 0

            if caster:
                filtered = filtered.filter(caster=caster)
            elif caster_in:
                filtered = filtered.filter(caster__in=to_list(caster_in))

            if payer:
                filtered = filtered.filter(payer=payer)
            elif payer_in:
                filtered = filtered.filter(payer__in=to_list(payer_in))

            """ Date """
            date = request.GET.get('date', 0)
            date_end = request.GET.get('date_end', 0)
            date_start = request.GET.get('date_start', 0)

            if date:
                filtered = filtered.filter(date__contains=date)

            else:
                if date_start:
                    filtered = filtered.filter(date__gte=date_start)

                if date_end:
                    filtered = filtered.filter(date__lte=date_end)

            """ Payee """
            payee = request.GET.get('payee', 0)
            payee_in = request.GET.get('payee_in', 0)
            if payee:
                filtered = filtered.filter(tickets__payee=payee).distinct()
            elif payee_in:
                filtered = filtered.filter(tickets__payee__in=to_list(payee_in)).distinct()

            """ Product """
            product = request.GET.get('product', 0)
            product_in = request.GET.get('product_in', 0)
            if product:
                filtered = filtered.filter(tickets__product=product).distinct()
            elif product_in:
                filtered = filtered.filter(tickets__product__in=to_list(product_in)).distinct()

            """ Price """
            price = request.GET.get('price', 0)
            price_in = request.GET.get('price_in', 0)
            if price:
                filtered = filtered.filter(tickets__price=price).distinct()
            elif price_in:
                filtered = filtered.filter(tickets__price__in=to_list(price_in)).distinct()


            def processData(data):
                # print (data[0])
                return OrderSerializer(data, many=True).data

            page = int(request.GET.get('page', 1))
            response_object['orders'] = paginate(filtered, page, processData) 

        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        response_object['message'] = 'Order introuvable'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        response_object['message'] = 'Une erreur est survenue'
        if e.args:
            response_object['message'] += ' ({})'.format(e.args[0])
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


""" List tickets - Filter by parameters """
@api_view(['GET'])
@login_required(['is_superuser', 'admin', 'parent'])
def api_tickets(request):
    response_object = {
        'status': 'Failure'
    }

    try:
        is_admin = False
        sibling = None
        
        if 'admin' in request.META['check']['role']:
            is_admin = True

        if 'parent' in request.META['check']['role']:
            sibling = Sibling.objects.get(parent=request.META['check']['id'])

        pk = request.GET.get('pk', 0)
        order_id = request.GET.get('order_id', 0)
        if pk:
            print (pk)
            ticket = Ticket.objects.get(pk=pk)
            response_object['ticket'] = TicketSerializer(ticket).data

        elif order_id:
            order = Order.objects.get(pk=order_id)
            response_object['tickets'] = TicketSerializer(order.tickets, many=True).data

        else:
            all = Ticket.objects.all()
            filtered = all

            to_list = lambda s: s.split(',')

            payer = request.GET.get('payer', 0)
            caster = request.GET.get('caster', 0)
            payer_in = request.GET.get('payer_in', 0)
            caster_in = request.GET.get('caster_in', 0)

            if caster:
                filtered = filtered.filter(order__caster=caster)
            elif caster_in:
                filtered = filtered.filter(order__caster__in=to_list(caster_in))

            if payer:
                filtered = filtered.filter(order__payer=payer)
            elif payer_in:
                filtered = filtered.filter(order__payer__in=to_list(payer_in))

            """ Date """
            date_end = request.GET.get('date_end', 0)
            date_start = request.GET.get('date_start', 0)

            if date_start:
                filtered = filtered.filter(order__date__gte=date_start)

            if date_end:
                filtered = filtered.filter(order__date__lte=date_end)

            """ Payee """
            payee = request.GET.get('payee', 0)
            payee_in = request.GET.get('payee_in', 0)

            if payee:
                filtered = filtered.filter(payee=payee)
            elif payee_in:
                filtered = filtered.filter(payee__in=to_list(payee_in))

            """ Product """
            product = request.GET.get('product', 0)
            product_in = request.GET.get('product_in', 0)

            if product:
                filtered = filtered.filter(product=product)
            elif product_in:
                filtered = filtered.filter(product__in=to_list(product_in))

            """ Price """
            price = request.GET.get('price', 0)
            price_in = request.GET.get('price_in', 0)

            if price:
                filtered = filtered.filter(price=price)
            elif price_in:
                filtered = filtered.filter(price__in=to_list(price_in))

            def processData(data):
                # print (data[0])
                return TicketSerializer(data, many=True).data

            page = int(request.GET.get('page', 1))
            response_object['orders'] = paginate(filtered, page, processData) 

        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        response_object['message'] = 'Reçu introuvable'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except Ticket.DoesNotExist:
        response_object['message'] = 'Prestation introuvable'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        response_object['message'] = 'Une erreur est survenue'
        if e.args:
            response_object['message'] += ' ({})'.format(e.args[0])
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


""" List tickets for shop -  """
@api_view(['GET'])
@login_required(['is_superuser', 'admin', 'parent'])
def api_tickets_shop(request, sy, child):
    pass


""" Cancel tickets """
@api_view(['POST'])
@login_required(['is_superuser', 'admin'])
def api_cancel_tickets (request):
    response_object = {'status': 'Failure'}

    if not request.data:
        response_object['message'] = 'Aucune donnée trouvée.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)
    if not data:
        response_object['message'] = 'Format de données incorrect.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    try:
        cancel_status = cancel_order(
            client=data['client'],
            caster=request.META['check']['id'],
            tickets_pks=data['tickets']
        )
    except Exception as e:
        return exception_to_response (e)

    response_object['status'] = 'Success'
    response_object['cancel_status'] = cancel_status
    return JsonResponse(response_object, status=status.HTTP_200_OK)


""" Cancel Order """
@api_view(['POST'])
@login_required(['is_superuser', 'admin'])
def api_cancel_order (request):
    response_object = {'status': 'Failure'}

    if not request.data:
        response_object['message'] = 'Aucune donnée trouvée.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)
    if not data:
        response_object['message'] = 'Format de données incorrect.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    try:
        cancel_status = cancel_order(
            client=data['client'],
            caster=request.META['check']['id'],
            order_pk=data['order_id'],
        )
    except Exception as e:
        return exception_to_response (e)

    response_object['status'] = 'Success'
    response_object['cancel_status'] = cancel_status
    return JsonResponse(response_object, status=status.HTTP_200_OK)


""" Release 1.5.2 """

@api_view(['POST'])
@login_required(['is_superuser', 'admin', 'parent'])
def api_order_verify(request):
    response_object = {
        'status': 'Failure'
    }
    if not request.data:
        response_object['message'] = 'Payload vide.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    try:
        # Payer/Parent check
        if not [x for x in ['admin', 'is_superuser'] if x in request.META['check']['role']]:
            if request.META['check']['id'] != data['payer']:
                raise ForbiddenException

        verify_response = OrderHelper.verify_order(data)
        print (verify_response)
    except Exception as e:
        return exception_to_response(e)

    response_object['status'] = 'Success'
    response_object.update(verify_response)
    return JsonResponse(response_object, status=status.HTTP_200_OK)

@api_view(['POST'])
@login_required(['is_superuser', 'admin', 'parent'])
def api_order_verify_soft(request):
    response_object = {
        'status': 'Failure'
    }
    if not request.data:
        response_object['message'] = 'Payload vide.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    try:
        # Payer/Parent check
        if not [x for x in ['admin', 'is_superuser'] if x in request.META['check']['role']]:
            if request.META['check']['id'] != data['payer']:
                raise ForbiddenException

        verify_response = OrderHelper.verify_order(data, True)
    except Exception as e:
        return exception_to_response(e)

    response_object['status'] = 'Success'
    return JsonResponse(response_object.update(verify_response), status=status.HTTP_200_OK)


""" Not used """
@api_view(['POST'])
@login_required(['is_superuser', 'admin'])
def api_order_create(request):
    response_object = {
        'status': 'Failure'
    }
    if not request.data:
        response_object['message'] = 'Payload vide.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    try:
        # Payer/Parent check
        if not [x for x in ['admin', 'is_superuser'] if x in request.META['check']['role']]:
            if request.META['check']['id'] != data['payer']:
                raise ForbiddenException
        
        # Can return 201 or 402
        response = OrderHelper.create_order(data)
    except Exception as e:
        return exception_to_response(e)

    response_object['status'] = 'Success'
    response_object['order'] = OrderSerializer(response['order']).data
    return JsonResponse(response_object, status=response['status'])

@api_view(['POST'])
@login_required(['is_superuser', 'admin', 'parent'])
def api_order_pay_instant(request):
    response_object = {
        'status': 'Failure'
    }
    if not request.data:
        response_object['message'] = 'Payload vide.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    try:
        is_admin = False
        if [x for x in ['admin', 'is_superuser'] if x in request.META['check']['role']]:
            is_admin = True

        response = OrderHelper.instant_pay_order(data, is_admin=is_admin)
        
    except Exception as e:
        return exception_to_response(e)

    response_object['status'] = 'Success'
    response_object['order'] = OrderSerializer(response['order']).data
    return JsonResponse(response_object, status=response['status'])


@api_view(['POST'])
@login_required(['is_superuser', 'admin', 'parent'])
def api_order_confirm(request):
    response_object = {
        'status': 'Failure'
    }
    if not request.data:
        response_object['message'] = 'Payload vide.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    try:
        is_admin = False
        if [x for x in ['admin', 'is_superuser'] if x in request.META['check']['role']]:
            is_admin = True

        if 'methods' in data:
            raise BadRequestException('Aucune méthode de paiement requise.')
        
        response = OrderHelper.create_order(data, is_admin=is_admin)
        
    except Exception as e:
        return exception_to_response(e)

    response_object['status'] = 'Success'
    response_object['order'] = OrderSerializer(response['order']).data
    return JsonResponse(response_object, status=response['status'])


@api_view(['POST'])
@login_required(['is_superuser', 'admin'])
def api_order_reserve(request):
    response_object = {
        'status': 'Failure'
    }
    if not request.data:
        response_object['message'] = 'Payload vide.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    try:
        is_admin = False
        if [x for x in ['admin', 'is_superuser'] if x in request.META['check']['role']]:
            is_admin = True

        if 'methods' in data:
            raise BadRequestException('Aucune méthode de paiement requise.')
        
        response = OrderHelper.create_order(data, order_status=StatusEnum.RESERVED, is_admin=is_admin)

    except Exception as e:
        return exception_to_response(e)

    response_object['status'] = 'Success'
    response_object['order'] = OrderSerializer(response['order']).data
    return JsonResponse(response_object, status=response['status'])


# TODO
@api_view(['POST'])
@login_required(['is_superuser', 'admin', 'parent'])
def api_order_pay(request, pk):
    """
    data is actualy methods 
    """
    response_object = { 'status': 'Failure' }

    if not request.data:
        response_object['message'] = 'Payload vide.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    try:
        is_admin = False
        if [x for x in ['admin', 'is_superuser'] if x in request.META['check']['role']]:
            is_admin = True

        order = Order.objects.get(pk=pk)
        order = OrderHelper.pay_order(order, data, is_admin=is_admin)

    except Order.DoesNotExist:
        response_object['message'] = 'Reçu introuvable.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        # print (e)
        return exception_to_response(e)

    response_object['status'] = 'Success'
    response_object['order'] = OrderSerializer(order).data
    return JsonResponse(response_object, status=status.HTTP_200_OK)


# @api_view(['POST'])
# def api_order_ipn (request):
#     if not request.data:
#         # response_object['message'] = 'Payload vide.'
#         return JsonResponse({'status': 'Failure'}, status=status.HTTP_400_BAD_REQUEST)

#     # 1 - Parse received data with payment_vads
#     #

#     # 2 - 

#     print (request.data)


#     return JsonResponse({'status': 'Success'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def api_order_test(request):
    return JsonResponse({'status': 'Success'}, status=status.HTTP_402_PAYMENT_REQUIRED)






""" Tmp """
@api_view(['GET'])
def products_stocks(request):
    products = Product.objects.filter(pk__gte=1000).order_by('id')
    return render(request, 'intern/Order/ProductsStocks.html', {'products': products})


""" 
Old 
"""


@api_view(['GET'])
def order_search(request, version):
    response_object = {
        'status': 'Failure'
    }
    try:
        GET = request.GET

        # ID search
        if 'id' in GET:
            order = Order.objects.get(id=GET.get('id'))
            response_object['status'] = 'Success'
            response_object['order'] = OrderSerializer(order).data
            return JsonResponse(response_object, status=status.HTTP_200_OK)


        response_object['message'] = 'Failed to understand your query.';
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except Order.DoesNotExist:
        response_object['message'] = 'Order does not exist.';
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        response_object['message'] = f'An exception has occured with error: {e}';
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def ticket_search(request, version):
    response_object = {
        'status': 'Failure'
    }
    try:
        GET = request.GET

        # ID search
        if 'id' in GET:
            ticket = Ticket.objects.get(id=GET.get('id'))
            response_object['status'] = 'Success'
            response_object['ticket'] = TicketSerializer(ticket).data
            return JsonResponse(response_object, status=status.HTTP_200_OK)

        # Product search
        if 'product' in GET:
            tickets = Ticket.objects.filter(product=GET.get('product'))
            response_object['status'] = 'Success'
            response_object['tickets'] = TicketSerializer(tickets, many=True).data
            return JsonResponse(response_object, status=status.HTTP_200_OK)        

        response_object['message'] = 'Failed to understand your query.';
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except Order.DoesNotExist:
        response_object['message'] = 'Ticket does not exist.';
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        response_object['message'] = f'An exception has occured with error: {e}';
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)





@api_view(['POST'])
def order_migration(request, version):
    response_object = {
        'status': 'Failed'
    }
    try:
        data = get_parsed_data(request.data)
        order = create_order_migration(data)
        if type(order) is str:
            response_object['message'] = order
            print(order)
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        response_object['order'] = order.id
        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_201_CREATED)

    except:
        response_object['message'] = 'An exception occured during the process.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


"""
Incoming
    comment
    order_type
    reference
    caster
    payer
    peri [{
        'product': int,
        'children': list
    }]
    alsh [{
        'child': int,
        'products': list
    }]

Outcoming
    name
    comment
    order_type
    reference
    caster
    payer
    amount
    tickets
    tickets_invalid
"""
@api_view(['POST'])
def order_verify(request, version):
    response_object = {
        'status': 'Failure',
    }
    try:
        data = get_parsed_data(request.data)

        verify_result = verify_order(data)
        if verify_result['status'] == 'Failure':
            response_object['message'] = verify_result['message']
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        if not len(verify_result['tickets']):
            response_object['message'] = 'No valid tickets.'
            return JsonResponse(response_object, status=status.HTTP_200_OK)

        # Add order id
        response_object['status'] = 'Success'
        response_object['order'] = {
            'name':             NAME,
            'comment':          data['comment'],
            'order_type':       data['order_type'],
            'reference':        data['reference'],
            'payer':            data['payer'],
            'caster':           data['caster'],
            'amount':           verify_result['amount'],
            'tickets':          verify_result['tickets'],
            'tickets_invalid':  verify_result['tickets_invalid'],
        }

        # Send response
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except (KeyError) as e:
        print('Not a valid POST request. ' + str(e))
        response_object['message'] = ('Not a valid POST request: %s key missing.' + str(e))
        

    except:
        print('Failed to create an entry.')
        response_object['message'] = 'Failed to create an entry.'

    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


"""
Useless - Creation now in order_confirm
"""
@api_view(['POST'])
def order_create(request, version):
    response_object = {
        'status': 'Failure',
    }

    try:
        data = get_parsed_data(request.data)

        verify_result = verify_order(data)
        if verify_result['status'] == 'Failure':
            response_object['message'] = verify_result['message']
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        if not len(verify_result['tickets']):
            response_object['message'] = 'No valid tickets.'
            return JsonResponse(response_object, status=status.HTTP_200_OK)


        payload = {
            'name':         NAME,
            'comment':      data['comment'],
            'order_type':   data['order_type'],
            'caster':       data['caster'],
            'payer':        data['payer'],
            'amount':       verify_result['amount'],
            'tickets':      verify_result['tickets']
        }

        order = create_order(payload)
        if type(order) is str:
            response_object['message'] = order
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        response_object['status'] = 'Success'

        # Add order id
        response_object['order'] = {
            'id': order.id,
            'name': NAME,
            'payer':            data['payer'],
            'caster':           data['caster'],
            'comment':          data['comment'],
            'order_type':       data['order_type'],
            'amount':           verify_result['amount'],
            'tickets':          verify_result['tickets'],
            'tickets_invalid':  verify_result['tickets_invalid'],
        }

        # Send response
        return JsonResponse(response_object, status=status.HTTP_201_CREATED)
        
    except (KeyError) as e:
        print('Not a valid POST request. ' + str(e))
        response_object['message'] = ('Not a valid POST request: %s key missing.' + str(e))

    except:
        print('Failed to create an entry.')
        response_object['message'] = 'Failed to create an entry.'

    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


"""
Incoming
    comment
    order_type
    reference
    caster
    payer
    methods [{
        'method': int,
        'amount': float
        'reference': str,
    }]
    peri [{
        'product': int,
        'children': list
    }]
    alsh [{
        'child': int,
        'products': list
    }]

Outcoming
    id
    status
"""
@api_view(['POST'])
def order_confirm(request, version):
    response_object = {
        'status': 'Failure',
    }
    try:
        data = get_parsed_data(request.data)

        verify_result = verify_order(data)
        if verify_result['status'] == 'Failure':
            response_object['message'] = verify_result['message']
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        # On invalid tickets cancel order
        if verify_result['tickets_invalid']:
            response_object['message'] = 'Some products are invalid. Please refresh your order.'
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        # On different amount cancel order
        amount = 0
        for method in data['methods']:
            amount += method['amount']

        if verify_result['amount'] != amount:
            response_object['message'] = 'Amount is invalid.'
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        # Create order
        payload = {
            'name':         NAME,
            'comment':      data['comment'],
            'reference':    data['reference'],
            'order_type':   data['order_type'],
            'caster':       data['caster'],
            'payer':        data['payer'],
            'methods':      data['methods'],
            'amount':       verify_result['amount'],
            'tickets':      verify_result['tickets']
        }

        order = create_order_(payload)
        if type(order) is str:
            response_object['message'] = order
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        response_object['status'] = 'Success'
        response_object['order'] = order.id

        # Send response
        return JsonResponse(response_object, status=status.HTTP_201_CREATED)

    except (KeyError):
        print('Not a valid POST request.')
        response_object['message'] = 'Not a valid POST request.'

    except Exception as e:
        print('Failed to create an entry with error: %s.' % e)
        response_object['message'] = ('Failed to create an entry with error: %s.' % e)

    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


"""
    Useless since we created order_verify
"""
@api_view(['POST'])
def order_create_test(request, version):
    response_object = {
        'status': 'Failure',
    }

    try:
        data = get_parsed_data(request.data)

        verify_result = verify_order(data)
        if verify_result['status'] == 'Failure':
            response_object['message'] = verify_result['message']
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        if not len(verify_result['tickets']):
            response_object['message'] = 'No valid tickets.'
            return JsonResponse(response_object, status=status.HTTP_200_OK)

        response_object['status'] = 'Success'
        print(verify_result)
        response_object['verify_result'] = verify_result
        return Response(response_object, status=status.HTTP_201_CREATED)

    except (KeyError):
        print('Not a valid POST request.')
        response_object['message'] = 'Not a valid POST request.'

    except:
        print('Failed to create an entry.')
        response_object['message'] = 'Failed to create an entry.'

    return Response(response_object, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def order_id(request, version, pk):
    response_object = {
        'status': 'Failure'
    }
    try:
        order = Order.objects.get(id=pk)
        serializer = OrderSerializer(order)

        response_object['status'] = 'Success'
        response_object['order'] = serializer.data
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        response_object['status'] = 'Failure'
        response_object['message'] = 'No order found.'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Exception as e:
        response_object['message'] = 'An exception occured with error: ' + str(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)
    
    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def order_date(request, version, date):
    response_object = {
        'status': 'Failure'
    }
    try:
        orders = Order.objects.filter(date__contains=date, order_type__gte=1, order_type__lte=2)
        serializer = OrderSerializer(orders, many=True)

        response_object['status'] = 'Success'
        response_object['orders'] = serializer.data
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        response_object['status'] = 'Failure'
        response_object['message'] = 'No order found.'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Exception as e:
        response_object['message'] = 'An exception occured with error: ' + \
            str(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def order_child_id(request, version, pk):
    response_object = {
        'status': 'Failure'
    }
    try:
        tickets = Ticket.objects.filter(payee=pk)
        serializer = TicketSerializer(tickets, many=True)

        response_object['status'] = 'Success'
        response_object['tickets'] = serializer.data
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Ticket.DoesNotExist:
        response_object['status'] = 'Success'
        response_object['tickets'] = []
        response_object['message'] = 'No ticket(s) found.'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Exception as e:
        response_object['message'] = 'An exception occured with error: ' + \
            str(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)
