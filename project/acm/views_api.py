from django.http import JsonResponse

from rest_framework import status
from rest_framework.decorators import api_view

from users.models import User
from users.serializers import UserSerializer
from users.decorators import login_required
from users.exceptions import exception_to_response, BadRequestException, ForbiddenException, NotFoundException

from params.models import SchoolYear

from order.models import Order
from order.serializers import OrderSerializer

from accounting.models import Client
from accounting.serializers import ClientSerializers

from registration.models import Sibling, SiblingChild, SiblingIntels, Record
from registration.serializers import IntelSerializer, RecordSerializer


def custom_serializer (parent, intels, children, records, client, order, orders):
    sy = SchoolYear.objects.get(is_active=True)

    _parent = UserSerializer(parent).data

    intel = intels.filter(school_year=sy.id).first()
    _intel = IntelSerializer(intel).data if intel else {}

    intels = intels.exclude(school_year=sy.id)
    _intels = IntelSerializer(intels, many=True).data if intels else {}

    _parent['intel'] = _intel
    _parent['intels'] = _intels

    _children = UserSerializer(children, many=True).data
    for child in _children:
        record = records.filter(child=child['id'], school_year=sy.id).first()
        child['record'] = RecordSerializer(record).data if record else {}

        _records = records.filter(child=child['id']).exclude(school_year=sy.id)
        child['records'] = RecordSerializer(_records, many=True).data if _records else {}

        # _parent['children'].append(child)

    _parent['client'] = ClientSerializers(client).data if client else {}

    _order = OrderSerializer(order).data if order else {}
    _orders = OrderSerializer(orders, many=True).data if orders else {}

    return (_parent, _children, _order, _orders)

@api_view(['GET'])
@login_required(['is_superuser', 'admin', 'parent'])
def api_shop (request, pk):
    response_object = {'status': 'Failure'}

    try:
        # print ('1')
        parent = User.objects.get(pk=pk)

        if parent.roles.filter(slug='parent'):
            sibling = Sibling.objects.get(parent=parent.id)

        elif parent.roles.filter(slug='child'):
            sibling = Sibling.objects.get(children__child=parent.id)
            parent = User.objects.get(pk=sibling.parent)
        else:
            raise BadRequestException('Aucun role trouvé pour cet utilisateur.')
        
        # print ('2')
        # Auth check
        if not [x for x in ['admin', 'is_superuser'] if x in request.META['check']['role']]:
            if request.META['check']['id'] != parent.id:
                raise ForbiddenException
            
        # print ('3')
        ids = [schild.child for schild in sibling.children.all()]

        # print ('4')
        children = User.objects.filter(pk__in=ids)
        records = Record.objects.filter(child__in=ids)        

        # print ('5')
        client = Client.objects.filter(id=parent.id).first()
        order = Order.objects.orders_waiting(payer=parent.id).first()
        orders = Order.objects.filter(payer=parent.id).exclude(pk=order.id if order else 0)

        response_object['status'] = 'Success'
        response_object['parent'], response_object['children'], response_object['order'], response_object['orders'] = custom_serializer(
            parent,
            sibling.intels.all(),
            children,
            records,
            client,
            order,
            orders
        )

        return JsonResponse(response_object, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        raise NotFoundException('Utilisateur introuvable.')
    
    except Sibling.DoesNotExist:
        raise NotFoundException('Famille introuvable.')

    except Exception as e:
        return exception_to_response (e)
