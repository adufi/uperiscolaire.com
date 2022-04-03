import json

from django.http import HttpRequest, JsonResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .utils import create_record, create_family, create_record_migration, create_family_migration, create_siblings_migration
from .models import Family, Record, Sibling, SiblingChild, SiblingIntels
from .serializers import FamilySerializer, RecordSerializer, RecordSerializerShort, SiblingSerializer, SiblingChildSerializer

from .utils import IntelHelper
from .serializers import IntelSerializer

from users.utils import InternalErrorException, BadRequestException, UnauthorizedException, ForbiddenException, NotFoundException, get_parsed_data
from users.decorators import login_required


def handle_exeptions(e, default='Une erreur est survenue.'):
    if e.args:
        return e.args[0]
    else:
        return default


""" 1.4 """
@api_view(['POST', 'PUT'])
@login_required(['is_superuser', 'admin', 'parent'])
def api_intel(request, pk=0):
    response_object = { 'status': 'Failure' }

    try:
        is_admin = False
        sibling = None
        
        if 'admin' in request.META['check']['role']:
            is_admin = True

        if 'parent' in request.META['check']['role']:
            sibling = Sibling.objects.get(parent=request.META['check']['id'])

        if request.method == 'POST':
            if not request.data:
                response_object['message'] = 'Aucune donnée trouvée.'
                return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

            data = get_parsed_data(request.data)

            if is_admin and 'parent_id' in data:
                sibling = Sibling.objects.get(parent=data['parent_id'])

            intel = IntelHelper.create(sibling, data, is_admin)

            # Serialize
            response_object['intels'] = IntelSerializer(sibling.intels.all(), many=True).data

        elif request.method == 'PUT':
            if not request.data:
                response_object['message'] = 'Aucune donnée trouvée.'
                return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

            data = get_parsed_data(request.data)

            intel = IntelHelper.update(sibling, data, pk, is_admin)
            intels = intel.sibling.intels.all()

            # Serialize
            response_object['intels'] = IntelSerializer(intels, many=True).data
            # response_object['intel'] = IntelSerializer(intel).data

        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)
        
    except BadRequestException as e:
        response_object['message'] = handle_exeptions(e, 'Payload invalid.')
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except ForbiddenException as e:
        response_object['message'] = handle_exeptions(e, 'Vous n\'êtes pas autorisé a accéder à cette ressource.')
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    except NotFoundException as e:
        response_object['message'] = handle_exeptions(e, 'Objet introuvable.')
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except (Sibling.DoesNotExist, SiblingIntels.DoesNotExist, InternalErrorException):
        response_object['message'] = 'Famille introuvable.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except KeyError as e:
        response_object['message'] = handle_exeptions(e, 'Erreur d\'index.')
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        response_object['message'] = handle_exeptions(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse(response_object, status=status.HTTP_405_METHOD_NOT_ALLOWED)

""" OLD """

@api_view(['GET'])
def siblings(request, version):
    pass


@api_view(['GET'])
def siblings_id(request, version, pk):
    response_object = {
        'status': 'Failure'
    }
    try:
        # Check authorizations
        # s = check_authorizations(request.headers, [])
        # if type(s) is str:
        #     response_object['message'] = 'You are not allowed to access this ressource.'
        #     return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

        siblings = Sibling.objects.get(id=pk)
        serializer = SiblingSerializer(siblings, read_only=True)

        # Serialize data and return them
        response_object['status'] = 'Success'
        response_object['siblings'] = serializer.data
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Sibling.DoesNotExist:
        response_object['message'] = 'Sibling does not exist.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except:
        response_object['message'] = 'An exception occured during the process.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def siblings_child_id(request, version, pk):
    response_object = {
        'status': 'Failure'
    }
    try:
        # Check authorizations
        # s = check_authorizations(request.headers, [])
        # if type(s) is str:
        #     response_object['message'] = 'You are not allowed to access this ressource.'
        #     return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

        child = SiblingChild.objects.get(child=pk)
        serializer = SiblingSerializer(child.sibling, read_only=True)

        # Serialize data and return them
        response_object['status'] = 'Success'
        response_object['siblings'] = serializer.data
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except SiblingChild.DoesNotExist:
        response_object['message'] = 'Sibling does not exist.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except:
        response_object['message'] = 'An exception occured during the process.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def siblings_parent_id(request, version, pk):
    response_object = {
        'status': 'Failure'
    }
    try:
        # Check authorizations
        # s = check_authorizations(request.headers, [])
        # if type(s) is str:
        #     response_object['message'] = 'You are not allowed to access this ressource.'
        #     return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

        siblings = Sibling.objects.get(parent=pk)
        serializer = SiblingSerializer(siblings, read_only=True)

        # Serialize data and return them
        response_object['status'] = 'Success'
        response_object['siblings'] = serializer.data
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Sibling.DoesNotExist:
        response_object['message'] = 'Sibling does not exist.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except:
        response_object['message'] = 'An exception occured during the process.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'POST'])
def families(request, version):
    response_object = {
        'status': 'Failure'
    }

    if request.method == 'GET':
        s = check_authorizations(request.headers, [])
        if type(s) is str:
            response_object['message'] = 'You are not allowed to access this ressource.'
            return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

        families = Family.objects.all()
        serializer = FamilySerializer(families, many=True, read_only=True)

        # Serialize data and return them
        response_object['status'] = 'Success'
        response_object['families'] = serializer.data
        return JsonResponse(response_object, status=status.HTTP_200_OK)


    elif request.method == 'POST':
        s = check_authorizations(request.headers, [])
        if type(s) is str:
            response_object['message'] = 'You are not allowed to access this ressource.'
            return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

        try:
            data = get_parsed_data(request.data)
            family = create_family(data)
            if type(family) is str:
                response_object['message'] = family
                return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

            response_object['family'] = family.id
            response_object['status'] = 'Success'
            return JsonResponse(response_object, status=status.HTTP_200_OK)

        except:
            response_object['message'] = 'An exception occured during the process.'
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def families_id(request, version, pk):
    response_object = {
        'status': 'Failure'
    }
    try:
        s = check_authorizations(request.headers, [])
        if type(s) is str:
            response_object['message'] = 'You are not allowed to access this ressource.'
            return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

        family = Family.objects.get(id=pk)
        serializer = FamilySerializer(family, read_only=True)

        # Serialize data and return them
        response_object['status'] = 'Success'
        response_object['record'] = serializer.data
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Family.DoesNotExist:
        response_object['message'] = 'Family does not exist.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except:
        response_object['message'] = 'An exception occured during the process.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'POST'])
def records(request, version):
    response_object = {
        'status': 'Failure'
    }

    if request.method == 'GET':
        s = check_authorizations(request.headers, [])
        if type(s) is str:
            response_object['message'] = 'You are not allowed to access this ressource.'
            return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

        records = Record.objects.all()
        serializer = RecordSerializer(records, many=True, read_only=True)

        # Serialize data and return them
        response_object['status'] = 'Success'
        response_object['records'] = serializer.data
        return JsonResponse(response_object, status=status.HTTP_200_OK)


        """ For local usage we passed this step """
        serializer = None

        s1 = check_authorizations(request.headers, ['admin', 'is_superuser'])
        if type(s1) is str:
            print('Error s1: ' + s1)

            s2 = check_authorizations(request.headers, [])
            print(f'Error s2: {s2}')
            if type(s2) is str:
                response_object['message'] = 'You are not allowed to access this ressource.'
                return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)


            records = Record.objects.all()
            serializer = RecordSerializerShort(records, many=True, read_only=True)

        else:
            records = Record.objects.all()
            serializer = RecordSerializer(records, many=True, read_only=True)

        # Check error on serializer
        if serializer == None:
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        # Serialize data and return them
        response_object['status'] = 'Success'
        response_object['records'] = serializer.data
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        # s = check_authorizations(request.headers, [])
        # if type(s) is str:
        #     response_object['message'] = 'You are not allowed to access this ressource.'
        #     return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

        # try:
        #     data = get_parsed_data(request.data)
        #     record = create_record(data)
        #     if type(record) is str:
        #         response_object['message'] = record
        #         return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        #     response_object['record'] = record.id
        #     response_object['status'] = 'Success'
        #     return JsonResponse(response_object, status=status.HTTP_200_OK)

        # except:
        #     response_object['message'] = 'An exception occured during the process.'
        #     return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)
        
        response_object['message'] = 'Service suspendu.'
        return JsonResponse(response_object, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def records_id(request, version, pk):
    response_object = {
        'status': 'Failure'
    }

    try:
        s = check_authorizations(request.headers, [])
        if type(s) is str:
            response_object['message'] = 'You are not allowed to access this ressource.'
            return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

        record = Record.objects.get(id=pk)
        serializer = RecordSerializer(record, read_only=True)

        # Serialize data and return them
        response_object['status'] = 'Success'
        response_object['record'] = serializer.data
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Record.DoesNotExist:
        response_object['message'] = 'Record does not exist.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except:
        response_object['message'] = 'An exception occured during the process.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    try:

        """ For local usage we passed this step """
        serializer = None

        s1 = check_authorizations(request.headers, ['admin', 'is_superuser'])
        if type(s1) is str:

            s2 = check_authorizations(request.headers, [])
            if type(s2) is str:
                print('Error: ' + s1)
                print('Error: ' + s2)
                response_object['message'] = 'You are not allowed to access this ressource.'
                return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

            records = Record.objects.all()
            serializer = RecordSerializerShort(
                records, many=True, read_only=True)

        else:
            records = Record.objects.all()
            serializer = RecordSerializer(records, read_only=True)

        response_object['status'] = 'Success'
        response_object['records'] = serializer.data
        return JsonResponse(response_object, status=status.HTTP_200_OK)
    
    except:
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def records_child_id(request, version, pk):
    response_object = {
        'status': 'Failure'
    }
    try:
        s = check_authorizations(request.headers, [])
        if type(s) is str:
            response_object['message'] = 'You are not allowed to access this ressource.'
            return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

        record = Record.objects.get(child_id=pk)
        serializer = RecordSerializer(record, read_only=True)

        # Serialize data and return them
        response_object['status'] = 'Success'
        response_object['record'] = serializer.data
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Record.DoesNotExist:
        response_object['message'] = 'Record does not exist.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except:
        response_object['message'] = 'An exception occured during the process.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)



""" MIGRATION """
@api_view(['POST'])
def records_migration(request, version):
    response_object = {
        'status': 'Failure'
    }
    try:
        data = get_parsed_data(request.data)
        record = create_record_migration(data)
        if type(record) is str:
            response_object['message'] = record
            print(response_object['message'])
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        response_object['record'] = record.id
        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Exception as e:
        response_object['message'] = 'An exception occured during the process. ' + str(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)
    
    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def families_migration(request, version):
    response_object = {
        'status': 'Failure'
    }
    try:
        data = get_parsed_data(request.data)
        family = create_family_migration(data)
        if type(family) is str:
            response_object['message'] = family
            print(response_object['message'])
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        response_object['family'] = family.id
        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Exception as e:
        response_object['message'] = 'An exception occured during the process. ' + str(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def siblings_migration(request, version):
    response_object = {
        'status': 'Failure'
    }
    try:
        data = get_parsed_data(request.data)
        siblings = create_siblings_migration(data)
        if type(siblings) is str:
            response_object['message'] = siblings
            print(response_object['message'])
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        response_object['siblings'] = siblings.id
        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Exception as e:
        response_object['message'] = 'An exception occured during the process. ' + str(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)
