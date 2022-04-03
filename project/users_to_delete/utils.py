import json

from django.conf import settings
from django.http import QueryDict, JsonResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import PermissionDenied

from rest_framework import status

from .models import UserAuth, User
from .serializers import UserSerializer
from .utils_registers import create_user, create_user_migration


PAGINATOR_MAX_PAGE = 25


def my_jwt_response_handler(token, user=None, request=None):
    user = request.user.user if hasattr(request.user, 'user') else None
    serializer = UserSerializer(user)
    return {
        'token': token,
        'user': UserSerializer(user, context={'request': request}).data
    }
    

def get_parsed_data(data):
    if not data:
        return False
    if type(data) is QueryDict:
        for x in data:
            try:
                return json.loads(x)
            except:
                return False
    return data


def paginate(querySet, page, processData=None):
    paginator = Paginator(querySet, PAGINATOR_MAX_PAGE)
    # page = int(request.GET.get('page', 1))

    try:
        paginator_page = paginator.get_page(page)
    except PageNotAnInteger:
        paginator_page = paginator.get_page(1)
    except EmptyPage:
        paginator_page = paginator.get_page(paginator.num_pages)

    # print (paginator_page[0])

    if processData:
        _data = processData(list(paginator_page))
        # _data = processData(paginator_page.object_list)
    else:
        _data = paginator_page

    data = {
        'count': paginator.count,
        'pages': paginator_page.paginator.num_pages,
        'data': _data,
        'has_next': paginator_page.has_next(),
        'has_previous': paginator_page.has_previous()
    }
    return data


"""
check_authorizations(request, []) => basic auth
check_authorizations(request, ['admin', 'is_superuser'])
"""
def check_authorizations(headers, roles):
    if 'Authorization' in headers:
        try:
            token = headers.get('Authorization').split(' ')[1]
        except Exception as e:
            raise PermissionDenied('Aucun token trouvé')
        return _check_authorizations(token, roles)
    else:
        raise PermissionDenied('Aucune authorisation trouvée')


"""
    For testing purpose
"""
def _check_authorizations(token, roles):
    try:
        id = UserAuth.decode_auth_token(token)

        # Invalid id
        if type(id) is str:
            raise PermissionDenied('ID invalide')

        auth = UserAuth.objects.get(id=id)

        # No user attached to auth - no roles
        if not hasattr(auth, 'user'):
            raise PermissionDenied('Aucun utilisateur associé à ces identifiants')

        # User authenticated
        if not roles:
            return {'role': '', 'id': auth.user.id}

        if 'is_superuser' in roles and auth.is_superuser:
            return {'role': 'is_superuser', 'id': auth.user.id}

        _roles = []
        for role in auth.user.roles.all():
            if role.slug in roles:
                _roles.append(role.slug)
        
        if _roles:
            return {'role': ' '.join(_roles), 'id': auth.user.id}

        raise PermissionDenied('Aucun role trouvé pour cet utilisateur')

    except UserAuth.DoesNotExist:
        raise PermissionDenied('Auth introuvable')

    except IndexError:
        raise PermissionDenied('Erreur d\'index')


def users_read(request, _users):
    page = int(request.GET.get('page', 1))
    paginator = Paginator(_users, PAGINATOR_MAX_PAGE)

    try:
        paginator_page = paginator.get_page(page)

    except PageNotAnInteger:
        paginator_page = paginator.get_page(1)
    
    except EmptyPage:
        paginator_page = paginator.get_page(paginator.num_pages)


    __users = UserSerializer(list(paginator_page), many=True)

    data = {
        'count': paginator.count,
        'pages': paginator_page.paginator.num_pages,
        'users': __users.data,
        'has_next': paginator_page.has_next(),
        'has_previous': paginator_page.has_previous()
    }
    return data


def list_users(_role = ''):
    if not _role:
        users = User.objects.all()
        return UserSerializer(users, many=True)
    else:
        users = User.objects.filter(roles__slug=_role)
        return UserSerializer(users, many=True)

        x = []
        for user in users:
            for role in user.roles.all():
                if role.slug == _role:
                    x.append(user)
        return UserSerializer(x, many=True)


def macro_get_users(headers, _role = ''):
    response_object = {
        'status': 'Failure',
    }
    # if not check_authorizations(headers, []):
    #     response_object['message'] = 'You are not allowed to access this ressource.'
    #     return response_object

    serializer = list_users(_role)
    response_object['users'] = serializer.data
    response_object['status'] = 'Success'
    return response_object


def get_parsed_data(data):
    if not data:
        return False

    if type(data) is QueryDict:
        for x in data:
            return json.loads(x)
    
    return data


def macro_create_user(request, roles):
    response_object = {
        'status': 'Failure',
    }
    if not check_authorizations(request.headers, ['superuser', 'admin', 'ap_admin']):
        response_object['message'] = 'You are not allowed to access this ressource.'
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    if not request.data:
        response_object['message'] = 'No request data.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    try:
        data = get_parsed_data(request.data)
        
        data['roles'] = roles
        print (data)

        user = create_user(data)
        print(f'user: {user}')

        if type(user) is str:
            response_object['message'] = user
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        response_object['user'] = user.id
        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except:
        response_object['message'] = 'Invalid payload.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


def macro_create_user_migration(request, roles):
    response_object = {
        'status': 'Failure',
    }
    if not check_authorizations(request.headers, ['superuser', 'admin', 'ap_admin']):
        response_object['message'] = 'You are not allowed to access this ressource.'
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    if not request.data:
        response_object['message'] = 'No request data.'
        print ('No request data.')
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    try:
        print(request.data)
        data = get_parsed_data(request.data)

        data['roles'] = roles
        print(data)

        user = create_user_migration(data)
        print(f'user: {user}')

        if type(user) is str:
            response_object['message'] = user
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        response_object['user'] = user.id
        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Exception as e:
        response_object['message'] = 'Invalid payload: ' + str(e)
        print ('Invalid payload. ' + str(e))
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    print('End of function.')
    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)
