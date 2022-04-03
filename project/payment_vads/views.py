from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view

from .parser import parse
from .models import TransactionVADS, OrderStatusEnum as OSE

from order.utils import OrderHelper
from users.utils import get_parsed_data
from users.exceptions import exception_to_response, BadRequestException
# from project.exceptions import exception_to_response

# Create your views here.

ALLOW_TESTS = True

# def parse (data):
#     pass

def vads_success (request):
    return render(request, 'client/Payment/PaymentSuccess.html')

def vads_error (request):
    return render(request, 'client/Payment/PaymentError.html')

@api_view(['POST'])
def api_vads_ipn (request):
    # print (request.META['REMOTE_HOST'])
    # print (request.META['REMOTE_ADDR'])

    if not request.data:
        # response_object['message'] = 'Payload vide.'
        return JsonResponse({'status': 'Failure'}, status=status.HTTP_400_BAD_REQUEST)

    data = request.data.dict()
    print (data)

    if not settings.DEBUG:
        if data['vads_ctx_mode'] != 'PRODUCTION':
            return JsonResponse({'status': 'Failure', 'message': 'Transaction TEST refusée'}, status=status.HTTP_400_BAD_REQUEST) 

    try:
        # 1 - Save transaction
        # print ('1')
        transaction = TransactionVADS.objects.create_transaction(data)

        if transaction.trans_status != 'AUTHORISED':
            raise BadRequestException('Paiement non authorisé.')

        # 2 - Parse received data with payment_vads
        # print ('2')
        parsed = parse(transaction.ext_info_1)

        print (transaction.ext_info_1)
        print (parsed)

        if not parsed['status']:
            raise Exception('payment.parser.parse_v1 returned False.')

    except Exception as e:
        return exception_to_response(e)

    # print (parsed)

    try:
        if parsed['version'] == 1:
            # 3 - Query order
            # raise BadRequest on error 
            # print ('3')
            res = OrderHelper.ipn_pay_v1({
                'cart': parsed['cart'],
                'payer': parsed['parent_id'],
                'amount': transaction.amount / 100,
                'transaction_id': transaction.id
            })

            # 4 - Attach order to transaction
            # print ('4')
            transaction.order_id = res['order'].id

        elif parsed['version'] == 2:
            order = OrderHelper.ipn_pay_v2({
                'order_id': parsed['order_id'],
                'amount': transaction.amount / 100,
                'transaction_id': transaction.id
            })

            transaction.order_id = order.id

        else:
            raise Exception

        transaction.order_status = OSE.COMPLETED
        transaction.save()

    except Exception as e:
        if str(e) == 'Création impossible: le panier contient des produits invalides.':
            transaction.order_status = OSE.INCORRECT_PRODUCT
        elif 'Montant incorrect.' in str(e):
            transaction.order_status = OSE.INCORRECT_AMOUNT
        else:
            transaction.order_status = OSE.INCORRECT_PAYLOAD

        transaction.order_message = str(e)
        transaction.save()

        # print (transaction.order_status)
        # print (transaction.order_message)

        return exception_to_response(e)

    return JsonResponse({'status': 'Success'}, status=status.HTTP_200_OK)