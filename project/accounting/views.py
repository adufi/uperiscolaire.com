import json
import requests

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .utils import set_credit, update_credit
from .forms import ClientForm, HistoryForm
from .models import Client, ClientCreditHistory, HistoryTypeEnum
from .serializers import ClientSerializers, CompleteClientSerializers, ClientCreditHistorySerializers

from users.utils import paginate, get_parsed_data, ForbiddenException
from users.decorators import login_required

from registration.models import Sibling

from params.models import Product, SchoolYear
from params.serializers import ProductSerializer

# Create your views here.

"""
GET Routes


POST Payload {
    type
    credit
    comment
}
"""
@api_view(['GET', 'POST'])
@login_required(['is_superuser', 'admin', 'parent'])
def api_clients(request, pk=0):
    response_object = { 'status': 'Failure' }

    try:
        is_admin = False

        if 'admin' in request.META['check']['role']:
            is_admin = True

        # if 'parent' in request.META['check']['role']:
        #     if pk:
        #         if pk != request.META['check']['id']:
        #             raise ForbiddenException

        if request.method == 'GET':
            history = request.GET.get('history', 0)

            if pk:
                if not is_admin and pk != request.META['check']['id']:
                    raise ForbiddenException

                client = Client.objects.filter(pk=pk)
                if client:
                    if history:
                        data = CompleteClientSerializers(client.first()).data
                    else:
                        data = ClientSerializers(client.first()).data

                else:
                    data = {}

                response_object['client'] = data

            else:
                clients = Client.objects.all()

                if history:
                    data = CompleteClientSerializers(clients, many=True).data
                else:
                    data = ClientSerializers(clients, many=True).data

                response_object['clients'] = [data]

            response_object['status'] = 'Success'
            return JsonResponse(response_object, status=status.HTTP_200_OK)

            # Admin - No pk specified
            # clients = Client.objects.all()

            # credit = request.GET.get('credit')
            # if credit:
            #     clients = clients.filter(credit=credit)

            # date_created = request.GET.get('date_created')
            # if date_created:
            #     clients = clients.filter(date_created=date_created)


            def processData(data):
                if history:
                    return CompleteClientSerializers(data, many=True).data
                else:
                    return ClientSerializers(data, many=True).data

            page = int(request.GET.get('page', 1))

            response_object['status'] = 'Success'
            response_object['clients'] = paginate(clients, page, processData) 
            return JsonResponse(response_object, status=status.HTTP_200_OK)

        elif request.method == 'POST':

            if not request.data:
                response_object['message'] = 'Aucune donnée trouvée.'
                return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

            print ('1')
            print (request.POST)

            data = get_parsed_data(request.data)
            data['caster'] = request.META['check']['id']
            
            response_object = set_credit(pk, data)

            if 'message' in response_object:
                return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)
            else:
                return JsonResponse(response_object, status=status.HTTP_200_OK)

    except ForbiddenException:
        response_object['message'] = 'Vous n\'êtes pas autorisé a accéder à cette ressource.'
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    except Client.DoesNotExist:
        response_object['message'] = 'Compte client introuvable.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except ClientCreditHistory.DoesNotExist:
        response_object['message'] = 'Historique du compte client introuvable.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except KeyError as e:
        response_object['message'] = f'Payload invalide avec erreur ({e.args[0]})'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        response_object['message'] = 'Une erreur est survenue'
        if e.args:
            response_object['message'] += ' ({})'.format(e.args[0])
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse(response_object, status=status.HTTP_405_METHOD_NOT_ALLOWED)


"""
POST payload {
    type
    caster
    comment
}
"""
@api_view(['POST'])
@login_required(['is_superuser', 'admin', 'parent'])
def api_credit_history(request, pk):
    response_object = {'status': 'Failure'}

    try:
        history = ClientCreditHistory.objects.get(pk=pk)

        if 'parent' in request.META['check']['role']:
            if history.client_id != request.META['check']['id']:
                raise ForbiddenException

        if not request.data:
            response_object['message'] = 'Aucune donnée trouvée.'
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        data = get_parsed_data(request.data)

        f = HistoryForm(data)
        if f.is_valid():
            history.update(
                data['type'],
                data['caster'],
                data['comment']
            )

            response_object['status'] = 'Success'
            response_object['client'] = CompleteClientSerializers(history.client).data
            return JsonResponse(response_object, status=status.HTTP_200_OK)

        else:
            response_object['errors'] = f.errors
            response_object['message'] = 'Formulaire historique incorrect.'
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except ForbiddenException:
        response_object['message'] = 'Vous n\'êtes pas autorisé a accéder à cette ressource.'
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    except ClientCreditHistory.DoesNotExist:
        response_object['message'] = 'Historique du compte client introuvable.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except KeyError as e:
        response_object['message'] = f'Payload invalide avec erreur ({f.args[0]})'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        response_object['message'] = 'Une erreur est survenue'
        if e.args:
            response_object['message'] += ' ({})'.format(e.args[0])
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)