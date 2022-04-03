import json

from django.http import JsonResponse
from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth import authenticate, login

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .utils import check_authorizations, users_read, macro_get_users, macro_create_user, macro_create_user_migration, get_parsed_data
from .utils_registers import create_parent, create_client, create_user
from .models import UserAuth, User, Role
from .serializers import AuthSerializerWithToken, UserSerializer

# Release 1.4
from .utils import UserHelper as uh, BadRequestException, ForbiddenException, NotFoundException, InternalErrorException
from .decorators import login_required

from registration.models import Sibling

from client_intern.utils import UserHelper, get_parsed_data

# Create your views here.


def home(request):
    try:
        print (request.GET.get('page')) 
        _users = User.objects.all()        

    except User.DoesNotExist as e:
        print ('Users not found')
        return JsonResponse(
            {
                'status': 'Failure',
                'message': 'Users not found.'
            }, 
            status=status.HTTP_400_BAD_REQUEST
        )

    data = users_read(request, _users)
    data['status'] = 'Success'
    return JsonResponse(data, status=status.HTTP_200_OK)


"""
Routes
    type    authenticate

    GET     admin       /users              List users
    GET     admin       /users/{id}         Get user with id
    POST    yes         /users              Create user
    
    GET     yes         /users/clients      Return clients
    POST    admin       /users/clients      Create client

    POST    no          /auth/login         Log user in
    POST    yes         /auth/logout        Log user out
    GET     yes         /auth/status        Get user status
    POST    no          /auth/register      Register user and return a token
"""

"""
Payload {
    'email'
    'password'
}
"""
@api_view(['POST'])
def auth_login(request):
    response_object = {
        'status': 'Failure',
        'message': 'Invalid payload.'
    }

    if not request.data:
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    try:
        data = request.data

        auth = authenticate(
            email=data['email'],
            password=data['password']
        )

        if auth is None:
            response_object['message'] = 'Invalid credentials.'
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        response_object['token'] = auth.token
        response_object['status'] = 'Success'

        if hasattr(auth, 'user'):
            response_object['user'] = auth.user.to_json()
            # serializer = UserSerializer(auth.user)
            # response_object['user'] = serializer.data
            
        else:
            response_object['user'] = {
                'auth': {'email': auth.email}
            }            

        del response_object['message']
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Exception as e:
        if e.args:
            response_object['message'] = 'Invalid payload with error: {}'.format(e.args[0])
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def auth_status(request):
    response_object = {
        'status': 'Failure',
    }
    try:
        token = request.headers.get('Authorization').split(' ')[1]
        id = UserAuth.decode_auth_token(token)
        if type(id) is str:
            # print ('TypeError with error: %s' % id)
            raise TypeError

        auth = UserAuth.objects.get(id=id)

        if hasattr(auth, 'user'):
            # serializer = UserSerializer(auth.user)
            response_object['user'] = auth.user.to_json()

        else:
            response_object['user'] = {
                'auth': {'email': auth.email}
            } 
        
        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except (UserAuth.DoesNotExist, TypeError):
        response_object['message'] = 'Invalid token.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except:
        response_object['message'] = 'Invalid payload.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


"""
NOTES
    Only parent can register this way
    Default role is 'parent'
    Payload {
        'email'
        'password1'
        'password2'
    }
"""
@api_view(['POST'])
def auth_register(request):
    print ('auth_register')

    response_object = {
        'status': 'Failure',
    }

    if not request.data:
        response_object['message'] = 'No request data.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    try:
        print ('1')
        user = UserHelper.register(data)
        print ('2')
        if type(user) is str:
            response_object['message'] = user
            print ('register() failed with error: ' + user)
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        print ('3')
        UserHelper.register_send_mail(request.get_host(), user.id, request.data.get('email', ''))

        print ('4')
        # response_object['user'] = UserSerializer(user).data
        response_object['user'] = user.to_json()
        response_object['token'] = user.auth.token
        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Exception as e:
        message = 'Invalid payload'
        if e.args:
            message += ' with error: ' + str(e.args[0])
        response_object['message'] = message
        print (message)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def _auth_register(request):
    response_object = {
        'status': 'Failure',
    }

    if not request.data:
        response_object['message'] = 'No request data.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    try: 
        user = create_parent(request.data)
        if type(user) is str:
            response_object['message'] = user
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        response_object['user'] = UserSerializer(user).data
        response_object['token'] = user.auth.token
        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except:
        response_object['message'] = 'Invalid payload.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


""" API USERS

As parent
---------
    GET /api/users/                 - FORBIDDEN
    GET /api/users/<pk>             - Get self or children by id - other is forbidden
    POST /api/user/             - Create intel for parent - Last school year
    PUT /api/user/<pk>          - Update self or children

As admin
---------
    GET /api/users/                 - List users (paginated)
    GET /api/users/<pk>             - Get user by id
    POST /api/user/             - Create an user
    PUT /api/user/<pk>          - Update user by pk

GET Parameters
--------------
    names
    roles -> role separated by comma e.g. admin,parent

POST Payload
------------
    parent_id

"""
@api_view(['GET', 'PUT'])
@login_required(['is_superuser', 'admin', 'parent'])
def api_users(request, pk=0):
    print ('api_users')
    response_object = {'status': 'Failure'}

    def macro_process_error (e):
        if e.args:
            response_object['message'] = e.args[0]

    try:
        is_admin = False
        sibling = None

        print(request.META['check'])
        if 'admin' in request.META['check']['role']:
            is_admin = True
        print('1')

        if 'parent' in request.META['check']['role']:
            sibling = Sibling.objects.filter(parent=request.META['check']['id']).first()
        print('2')

        if not is_admin and not sibling:
            raise InternalErrorException('Une erreur est survenue.')

        if request.method == 'GET':
            if pk:
                _ = uh.read_by_pk(sibling, pk, is_admin)
                response_object['user'] = UserSerializer(_).data

            else:
                if is_admin:
                    _ = uh.read(request.GET)
                    response_object['users'] = _
                else:
                    raise ForbiddenException('Vous n\'êtes pas autorisé à consulter cette page.')
            
            response_object['status'] = 'Success'
            return JsonResponse(response_object, status=status.HTTP_200_OK)

        # POST
        # Only for child
        # Parent ID required on admin request
        #
        # EDIT
        # POST route closed
        # For parent creation see registration
        # For child see children route
        elif request.method == 'POST':
            if not request.data:
                response_object['message'] = 'Aucune donnée trouvée.'
                return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

            data = get_parsed_data(request.data)

            user = uh.create(sibling, data, is_admin)
            response_object['user'] = user.to_json()

        # PUT
        elif request.method == 'PUT':
            if not pk:
                raise BadRequestException('Aucun ID spécifié.')

            if not request.data:
                raise BadRequestException('Aucune donnée trouvée.')

            data = get_parsed_data(request.data)
            _ = uh.update(sibling, pk, data, is_admin)
            response_object['user'] = UserSerializer(_).data

            response_object['status'] = 'Success'
            return JsonResponse(response_object, status=status.HTTP_200_OK)

        # response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    except Sibling.DoesNotExist:
        response_object['message'] = 'Famille inconnue.'
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 

    except Sibling.MultipleObjectsReturned:
        response_object['message'] = 'Multiples familles retrouvées.'
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except BadRequestException as e:
        response_object['message'] = e.args[0]
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except ForbiddenException as e:
        response_object['message'] = e.args[0]
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    except NotFoundException as e:
        response_object['message'] = e.args[0]
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except InternalErrorException as e:
        response_object['message'] = e.args[0]
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        response_object['message'] = 'Une erreur est survenue.'
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)



    # except (NoAuthorizationFound, UnauthorizedException, UserHelper.Unauthorized) as e:
    #     response_object['message'] = 'Vous n\'êtes pas autorisé à consulter cette page.'
    #     if e.args:
    #         response_object['message'] += ' ({})'.format(e.args[0])
    #     # print (response_object)
    #     return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)


    # except UserHelper.BadRequestException as e:
    #     macro_process_error(e)
    #     return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    # except UserHelper.ForbiddenException as e:
    #     macro_process_error(e)
    #     return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    # except UserHelper.NotFoundException as e:
    #     macro_process_error(e)
    #     return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    # except UserHelper.InternalErrorException as e:
    #     macro_process_error(e)
    #     return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # except Exception as e:
    #     response_object['message'] = 'Une erreur est survenue.'
    #     macro_process_error(e)
    #     return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    # except User.DoesNotExist:
    #     response_object['message'] = 'User does not exist'
    #     return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND) 

    # except UserHelper.SiblingNotSet:
    #     response_object['message'] = 'Sibling is not set'
    #     return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND) 

    # except SiblingIntels.DoesNotExist:
    #     response_object['message'] = 'Intel does not exist'
    #     if 'parent' in check['role']:
    #         response_object['message'] = 'Intel is not bound to parent'
    #     return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    # # create_intel
    # except InvalidPayloadException as e:
    #     response_object['message'] = 'Invalid payload'
    #     macro_process_error(e)
    #     return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    # except SchoolYear.DoesNotExist:
    #     response_object['message'] = 'Registration closed for this period'
    #     return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


""" API CHILDREN

As parent
---------
    GET /api/users/                 - FORBIDDEN
    GET /api/users/<pk>             - Get self or children by id - other is forbidden
    POST /api/user/                 - Create intel for parent - Last school year
    PUT /api/user/<pk>              - Update self or children

As admin
---------
    GET /api/users/                 - List users (paginated)
    GET /api/users/<pk>             - Get user by id
    POST /api/user/             - Create an user
    PUT /api/user/<pk>          - Update user by pk

GET Parameters
--------------
    names
    roles -> role separated by comma e.g. admin,parent

POST Payload
------------
    parent_id

"""
@api_view(['GET', 'POST', 'PUT'])
@login_required(['is_superuser', 'admin', 'parent'])
def api_children(request, pk=0):
    response_object = {'status': 'Failure'}

    def macro_process_error (e):
        if e.args:
            response_object['message'] = e.args[0]

    try:
        is_admin = False
        sibling = None

        if 'admin' in request.META['check']['role']:
            is_admin = True

        if 'parent' in request.META['check']['role']:
            sibling = Sibling.objects.get(parent=request.META['check']['id'])

        if not is_admin and not sibling:
            raise InternalErrorException('Une erreur est survenue.')

        if request.method == 'GET':
            if pk:
                _ = uh.read_child_by_pk(sibling, pk, is_admin)
                response_object['child'] = UserSerializer(_).data

            else:
                if is_admin:
                    _ = uh.read_children(request.GET)
                    response_object['children'] = _
                else:
                    raise ForbiddenException('Vous n\'êtes pas autorisé à consulter cette page.')
            
            response_object['status'] = 'Success'
            return JsonResponse(response_object, status=status.HTTP_200_OK)

        # POST
        # Only for child
        # Parent ID required on admin request
        elif request.method == 'POST':
            # if not request.data:
            #     response_object['message'] = 'Aucune donnée trouvée.'
            #     return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

            # data = get_parsed_data(request.data)

            # user = uh.create_child(sibling, data, is_admin)

            # response_object['child'] = UserSerializer(user).data
            # response_object['status'] = 'Success'
            response_object['message'] = 'Service suspendu.'
            return JsonResponse(response_object, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # PUT
        elif request.method == 'PUT':
            if not pk:
                raise BadRequestException('Aucun ID spécifié.')

            if not request.data:
                raise BadRequestException('Aucune donnée trouvée.')

            user = uh.read_child_by_pk(sibling, pk, is_admin)

            data = get_parsed_data(request.data)

            user = uh.update_child(user, data)

            response_object['child'] = UserSerializer(user).data

            response_object['status'] = 'Success'
            return JsonResponse(response_object, status=status.HTTP_200_OK)

        # response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    except Sibling.DoesNotExist:
        response_object['message'] = 'Famille inconnue.'
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 

    except Sibling.MultipleObjectsReturned:
        response_object['message'] = 'Multiples familles retrouvées.'
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except BadRequestException as e:
        response_object['message'] = e.args[0]
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except ForbiddenException as e:
        response_object['message'] = e.args[0]
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    except NotFoundException as e:
        response_object['message'] = e.args[0]
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except InternalErrorException as e:
        response_object['message'] = e.args[0]
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        response_object['message'] = 'Une erreur est survenue.'
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)



    # except (NoAuthorizationFound, UnauthorizedException, UserHelper.Unauthorized) as e:
    #     response_object['message'] = 'Vous n\'êtes pas autorisé à consulter cette page.'
    #     if e.args:
    #         response_object['message'] += ' ({})'.format(e.args[0])
    #     # print (response_object)
    #     return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)


    # except UserHelper.BadRequestException as e:
    #     macro_process_error(e)
    #     return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    # except UserHelper.ForbiddenException as e:
    #     macro_process_error(e)
    #     return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    # except UserHelper.NotFoundException as e:
    #     macro_process_error(e)
    #     return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    # except UserHelper.InternalErrorException as e:
    #     macro_process_error(e)
    #     return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # except Exception as e:
    #     response_object['message'] = 'Une erreur est survenue.'
    #     macro_process_error(e)
    #     return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    # except User.DoesNotExist:
    #     response_object['message'] = 'User does not exist'
    #     return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND) 

    # except UserHelper.SiblingNotSet:
    #     response_object['message'] = 'Sibling is not set'
    #     return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND) 

    # except SiblingIntels.DoesNotExist:
    #     response_object['message'] = 'Intel does not exist'
    #     if 'parent' in check['role']:
    #         response_object['message'] = 'Intel is not bound to parent'
    #     return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    # # create_intel
    # except InvalidPayloadException as e:
    #     response_object['message'] = 'Invalid payload'
    #     macro_process_error(e)
    #     return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    # except SchoolYear.DoesNotExist:
    #     response_object['message'] = 'Registration closed for this period'
    #     return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)




""" Everything below is old and probably not used """

"""
GET - Return every users
"""
@api_view(['GET'])
def users(request):
    if request.method == 'GET':
        r = macro_get_users(request.headers)
        if r['status'] == 'Failure':
            return JsonResponse(r, status=status.HTTP_401_UNAUTHORIZED)

        return JsonResponse(r, status=status.HTTP_200_OK)

    if request.method == 'POST':
        return macro_create_user(request, ['client'])
    
    return JsonResponse({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


"""
GET - Return an user by his id
"""
@api_view(['GET'])
def users_id(request, id):
    response_object = {
        'status': 'Failure'
    }
    # print (request.headers)
    if not check_authorizations(request.headers, ['superuser', 'admin', 'ap_admin']):
        response_object['message'] = 'You are not allowed to access this ressource.'
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    try:
        u = User.objects.get(id=id)
        serializer = UserSerializer(u)

        response_object['status'] = 'Success'
        response_object['user'] = serializer.data
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        response_object['message'] = 'User doesn\'t exist.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except:
        response_object['message'] = 'An error occured during process.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)


"""
GET - Perform a search on users
"""
@api_view(['GET'])
def users_search(request):
    response_object = {
        'status': 'Failure'
    }

    get = request.GET
    
    try:
        _users = None

        if 'role' in get:
            role = get.get('role', '')
            _users = User.objects.filter(roles__slug=role)

    except Exception as e:
        print ('An exception occured with error: {}.'.format(str(e)))
        response_object['message'] = 'An exception occured.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    if _users:
        data = users_read(request, _users)
        data['status'] = 'Success'
        return JsonResponse(data, status=status.HTTP_200_OK)
    
    response_object['message'] = 'No query specified.'
    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


"""
GET - Return a list payers 
POST - Create a payer
"""
@api_view(['GET', 'POST'])
def users_payers(request):
    if request.method == 'GET':
        r = macro_get_users(request.headers, 'payer')
        if r['status'] == 'Failure':
            return JsonResponse(r, status=status.HTTP_401_UNAUTHORIZED)

        return JsonResponse(r, status=status.HTTP_200_OK)

    if request.method == 'POST':
        return macro_create_user(request, ['payer'])

    return JsonResponse({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


"""
GET - Return a list children 
POST - Create a child
"""
@api_view(['GET', 'POST'])
def users_children(request):
    if request.method == 'GET':
        r = macro_get_users(request.headers, 'child')
        if r['status'] == 'Failure':
            return JsonResponse(r, status=status.HTTP_401_UNAUTHORIZED)

        return JsonResponse(r, status=status.HTTP_200_OK)

    if request.method == 'POST':
        return macro_create_user(request, ['child'])

    return JsonResponse({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


"""
GET - Return a list of parent - 
POST - Create a parent
"""
@api_view(['GET', 'POST'])
def users_parents(request):
    if request.method == 'GET':
        r = macro_get_users(request.headers, 'parent')
        if r['status'] == 'Failure':
            return JsonResponse(r, status=status.HTTP_401_UNAUTHORIZED)

        return JsonResponse(r, status=status.HTTP_200_OK)

    if request.method == 'POST':
        return macro_create_user(request, ['parent'])

    return JsonResponse({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


"""
GET - Return a list of client
POST - Create a new client in payment process
"""
@api_view(['GET', 'POST'])
def users_clients(request):
    if request.method == 'GET':
        r = macro_get_users(request.headers, 'client')
        if r['status'] == 'Failure':
            return JsonResponse(r, status=status.HTTP_401_UNAUTHORIZED)

        return JsonResponse(r, status=status.HTTP_200_OK)
        
    if request.method == 'POST':
        return macro_create_user(request, ['client'])

    return JsonResponse({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


""" Special Migration - Data ID required """
"""
GET - Return a list children
POST - Create a child
"""
@api_view(['POST'])
def users_children_migration(request):
    if request.method == 'POST':
        return macro_create_user_migration(request, ['child'])

    return JsonResponse({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


"""
GET - Return a list of parent -
POST - Create a parent
"""
@api_view(['POST'])
def users_parents_migration(request):
    if request.method == 'POST':
        return macro_create_user_migration(request, ['parent'])

    return JsonResponse({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


"""
GET - Return a list of payer -
POST - Create a payer
"""
@api_view(['POST'])
def users_payers_migration(request):
    if request.method == 'POST':
        return macro_create_user_migration(request, ['payer'])

    return JsonResponse({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
