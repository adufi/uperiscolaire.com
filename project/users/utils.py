import json
import pytz

from datetime import datetime

from django.db import transaction
from django.conf import settings
from django.http import QueryDict, JsonResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import PermissionDenied
from django.contrib import messages

from rest_framework import status, permissions

from .forms import ChildForm, UserForm
from .models import User, Role, UserAddress, UserPhones, UserEmail, UserAuth, CITIES, UserAddressType
from .serializers import UserSerializer
from .utils_registers import create_user, create_user_migration

from registration.models import Sibling, SiblingChild, Family

PAGINATOR_MAX_PAGE = 25


""" Exceptions """
# 400
class BadRequestException(Exception):
    pass

# 401
class UnauthorizedException(Exception):
    pass

# 403
class ForbiddenException(Exception):
    pass

# 404
class NotFoundException(Exception):
    pass

# 500
class InternalErrorException(Exception):
    pass


""" Utils """
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

""" Convert a normal string in a slug """
def set_slug(string):
    def purge_accents (strAccents):
        strAccents = list(strAccents)
        strAccentsOut = []
        accents = 'ÀÁÂÃÄÅàáâãäåÒÓÔÕÕÖØòóôõöøÈÉÊËèéêëðÇçÐÌÍÎÏìíîïÙÚÛÜùúûüÑñŠšŸÿýŽž'
        accentsOut = "AAAAAAaaaaaaOOOOOOOooooooEEEEeeeeeCcDIIIIiiiiUUUUuuuuNnSsYyyZz"
        for i, letter in enumerate(strAccents):
            index = accents.find(strAccents[i])
            if index != -1:
                strAccentsOut.append(accentsOut[index])
            else:
                strAccentsOut.append(strAccents[i])
            
        strAccentsOut = ''.join(strAccentsOut)
        return strAccentsOut

    raw = string.lower()
    raw = raw.replace(' ', '')
    raw = raw.replace('-', '')

    return purge_accents(raw)

def _localize(date):
    if type(date) is str:
        _ = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    else:
        _ = date
    return pytz.utc.localize(_)


"""
check_authorizations(request, []) => basic auth
check_authorizations(request, ['admin', 'is_superuser'])
"""
def check_authorizations(headers, roles):
    if 'Authorization' in headers:
        try:
            token = headers.get('Authorization').split(' ')[1]
        except Exception as e:
            raise UnauthorizedException('Aucun token trouvé.')
        return _check_authorizations(token, roles)
    else:
        raise UnauthorizedException('Aucune autorisation trouvée.')


"""
    For testing purpose
"""
def _check_authorizations(token, roles):
    try:
        id = UserAuth.decode_auth_token(token)

        # Invalid id
        if type(id) is str:
            raise UnauthorizedException(id)

        auth = UserAuth.objects.get(id=id)

        # No user attached to auth - no roles
        if not hasattr(auth, 'user'):
            raise UnauthorizedException('Aucun utilisateur associé à ces identifiants')

        # User authenticated
        if not roles:
            return {'role': '', 'id': auth.user.id}

        _roles = []
        if 'is_superuser' in roles and auth.is_superuser:
            _roles.append('is_superuser')

        for role in auth.user.roles.all():
            if role.slug in roles:
                _roles.append(role.slug)
        
        if _roles:
            return {'role': ' '.join(_roles), 'id': auth.user.id}

        raise ForbiddenException('Vous n\'êtes pas autorisé à consulter cette ressource.')
        # raise ForbiddenException('Aucun role trouvé pour cet utilisateur')

    except UserAuth.DoesNotExist:
        raise UnauthorizedException('Auth introuvable')

    except IndexError:
        raise UnauthorizedException('Erreur d\'index')


""" User Helper """
class UserHelper:
    
    """ Admin """
    @staticmethod
    def read(GET=None):
        users = User.objects.all()

        names = GET.get('names', '')
        roles = GET.get('roles', '')

        if roles:
            for role in roles.split(','):
                users = users.filter(roles__slug=role)

        if names:
            users = UserHelper.read_search_name(users, names)

        # paginate results
        def processData(data):
            # print (data[0])
            return [x.to_json() for x in data]

        page = int(GET.get('page', 1))
        return paginate(users, page, processData)
    
    """ Sibling is checked for parent """
    @staticmethod
    def read_by_pk(sibling, pk, is_admin=False):
        try:
            if not is_admin and pk != sibling.parent:
                # Trigger exception if child is not bound
                sibling.children.get(child=pk)
            
            return User.objects.get(pk=pk)

        except User.DoesNotExist:
            raise NotFoundException('Utilisateur introuvable.')

        # Raise 403 Forbidden
        except SiblingChild.DoesNotExist:
            pass

        # 403 Forbidden
        raise ForbiddenException('Vous n\'êtes pas autorisé à consulter cette page.')
    
    @staticmethod
    def read_search_name(querySet, names):
        names_list = names.split(',')
        users = []

        for name in names_list:
            __ = querySet.filter(slug__icontains=set_slug(name))
            for _ in __:
                found = False
                for user in users:
                    if _.id == user.id:
                        found = True
                if not found:
                    users.append(_)

        for name in names_list:
            __ = querySet.filter(emails__email__icontains=name)
            for _ in __:
                found = False
                for user in users:
                    if _.id == user.id:
                        found = True
                if not found:
                    users.append(_)

        return users

    # Hotfix 1.4.1
    @staticmethod
    def read_children(GET={}):
        users = User.objects.filter(roles__slug='child')

        # paginate results
        def processData(data):
            # print (data[0])
            return [x.to_json() for x in data]

        page = int(GET.get('page', 1))
        return paginate(users, page, processData)

    # Hotfix 1.4.1
    @staticmethod
    def read_child_by_pk(sibling, pk, is_admin=False):
        try:
            if not is_admin and pk != sibling.parent:
                # Trigger exception if child is not bound
                sibling.children.get(child=pk)
            
            return User.objects.get(roles__slug='child', pk=pk)

        except User.DoesNotExist:
            raise NotFoundException('Enfant introuvable.')

        # Raise 403 Forbidden
        except SiblingChild.DoesNotExist:
            pass

        # 403 Forbidden
        raise ForbiddenException('Vous n\'êtes pas autorisé à consulter cette page.')
    

    """ Child only """
    @staticmethod
    def create_child(sibling, data, is_admin):
        """
        Parameters
        ----------
        data {
            parent_id

            dob
            gender
            birthplace
            last_name
            first_name
        }

        Notes
        -----
            Create user
            Add role
            Register sibling
                Create if not exist
            Register family
        """

        # Sibling check
        if is_admin:
            if 'parent_id' in data:
                sibling = Sibling.objects.get(parent=data['parent_id'])
        
        # Admin sibling can be false
        if not sibling:
            raise InternalErrorException('Impossible de récupérer la famille.')

        f = ChildForm(data)
        if not f.is_valid():
            raise BadRequestException('Le formulaire contient des erreurs.', f.errors)

        sid = transaction.savepoint()
        try:
            user = User()

            id = User.objects.latest('id').id + 1

            user.id = id
            user.dob = f.cleaned_data['dob']
            user.gender = f.cleaned_data['gender']
            user.last_name = f.cleaned_data['last_name']
            user.first_name = f.cleaned_data['first_name']
            user.birthplace = f.cleaned_data['birthplace']

            user.date_completed = datetime.now()        
            user.save()

            user.roles.add(Role.objects.get(slug='child'))

            sibling.add_child(user.id)
            Family.objects.create(
                child=user.id,
                parent=sibling.parent
            )

            transaction.savepoint_commit(sid)
            return user

        except Sibling.DoesNotExist:
            raise BadRequestException('Impossible de récupérer la famille.')

        except Role.DoesNotExist:
            raise InternalErrorException('Role introuvable.')
        
        except InternalErrorException as e:
            raise e

        except BadRequestException as e:
            raise e

        except KeyError as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                raise BadRequestException('Clé invalide ({}).'.format(str(e.args[0])))
            raise BadRequestException('Clé invalide')

        except Exception as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                raise InternalErrorException('Payload invalide ({})'.format(e.args[0]))
            raise InternalErrorException('Payload invalide')
        
        raise BadRequestException('Une erreur est survenue.')

    """ TODO """
    @staticmethod
    @transaction.atomic
    def create(data, id=0):
        """
        Parameters
        ----------
        arg1: dict {
            id                  - Optional
            last_name          
            first_name
            accept_newsletter

            online_id           - Optional
            dob                 - Optional - Year-month-day
            is_active           - Optional - default True
            is_auto_password    - Optional - default False

            date_created?       - auto
            date_confirmed?     - auto
            date_completed?     - auto

            roles []            
                role (slug)     - str
            
            email               - Optional
            phones              - Optional
                cell
                home
                pro
            address             - Optional
                address1
                address2
                zip_code
                city
        }

        Returns
        -------
        """
        error = ''
        sid = transaction.savepoint()

        if not id:
            try:
                id = User.objects.latest('id').id + 1
            except:
                id = 1

        try:
            error = 'Failed to create user'

            user = User.objects.create(
                id=id,
                first_name=data['first_name'],
                last_name=data['last_name'],
                dob=data.get('dob', None),
                gender=data['gender'],
                birthplace=data['birthplace'],
                online_id=data.get('online_id', 0),
                is_active=data.get('is_active', True),
                is_auto_password=data.get('is_auto_password', False)
            )
            # Slug test
            user.set_slug()
            
            if len(User.objects.filter(slug=user.slug)) > 1:
                raise UserHelper.BadRequestException('Slug already exist')

            """ Add secondary intels (addresses, phones) """
            # Roles
            error = 'Failed to create roles'
            if 'roles' in data:
                # Add roles
                for slug in data['roles']:
                    try:
                        role = Role.objects.get(slug=slug)
                    except Role.DoesNotExist:
                        raise Exception('Role doesn\'t exist')
                    except:
                        raise Exception('An exception occured during role process')
                    user.roles.add(role)

            # Phone
            error = 'Failed to create phone'
            if 'phone' in data and data['phone']:
                user.phones.create(
                    phone=data['phone'],
                    is_main=True,
                    phone_type=UserPhoneType.MAIN,
                    user=user
                )

            # Email
            error = 'Failed to create emails'
            if 'email' in data and data['email']:

                # Test email occurence
                if UserEmail.objects.filter(email=data['email']):
                    raise Exception('Email already exist')

                user.emails.create(
                    email=data['email'],
                    is_main=True,
                    email_type=UserEmailType.HOME,
                    user=user
                )
            
            # Address
            error = 'Failed to create addresses'
            if 'address' in data and data['address']:
                user.addresses.create(
                    city=data['address']['city'],
                    address1=data['address']['address1'],
                    address2=data['address']['address2'],
                    zip_code=data['address']['zip_code'],
                    
                    is_main=True,
                    country='Martinique',
                    address_type=UserAddressType.HOME,
                    user=user,
                )

            transaction.savepoint_commit(sid)
            return user

        except Exception as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                return e.args[0]
            return f'An exception occured with error: {error}'

        return 'End of function.'


    @staticmethod
    def update(sibling, pk, data, is_admin=False):
        """
        Parameters
        ----------
        data {
            phones {
                cell
                home
                pro
            }
        }
        """
        try:
            if not is_admin and pk != sibling.parent:
                # Trigger exception if child is not bound
                sibling.children.get(child=pk)

            user = User.objects.get(pk=pk)

            if user.roles.filter(slug='child'):
                return UserHelper.update_child(user, data, is_admin)
            else:
                return UserHelper.update_user(user, data, is_admin)
        
        except User.DoesNotExist:
            raise NotFoundException('Utilisateur introuvable.')
        
        except Sibling.DoesNotExist:
            pass

        except Exception as e:
            raise BadRequestException(e.args[0])

        raise ForbiddenException('Vous n\'êtes pas autorisé à consulter cette page.')

    
    """ Update parent/user """
    @staticmethod
    @transaction.atomic
    def update_user(user, data, is_admin):
        """
        TODO
        Lighten process by making some attributes optionals
        """
        sid = transaction.savepoint()

        f = UserForm(data)
        if not f.is_valid():
            print (f.errors)
            raise BadRequestException('Formulaire incorrect', f.errors)

        def if_not_false(v, k):
            return f.cleaned_data[k] if f.cleaned_data[k] else v 
            # if f.cleaned_data[k]:
            #     v = f.cleaned_data[k]

        try:
            slug = set_slug(f.cleaned_data['last_name'] + f.cleaned_data['first_name'])

            if User.objects.filter(slug=slug).exclude(id=user.id):
                raise BadRequestException('L\'utilisateur existe déjà (Noms déjà utilisés).')

            user.gender     = f.cleaned_data['gender']
            user.last_name  = f.cleaned_data['last_name']
            user.first_name = f.cleaned_data['first_name']

            # Optional
            user.job = if_not_false(user.job, 'job')
            user.accept_newsletter = if_not_false(user.accept_newsletter, 'accept_newsletter')

            if is_admin:                
                user.dob = f.cleaned_data['dob']             # if_not_false(user.dob, 'dob')

                # Dates
                user.date_created       = if_not_false(user.date_created, 'date_created')         # f.cleaned_data['date_created']
                user.date_confirmed     = if_not_false(user.date_confirmed, 'date_confirmed')     # f.cleaned_data['date_confirmed']
                user.date_completed     = if_not_false(user.date_completed, 'date_completed')     # f.cleaned_data['date_completed']

                # Booleans
                # user.is_active          = f.cleaned_data['is_active']        # if_not_false(user.is_active, 'is_active')
                # user.is_auto_password   = f.cleaned_data['is_auto_password'] # if_not_false(user.is_auto_password, 'is_auto_password')

                """ Email can't change the regular way """                
                """
                if f.cleaned_data.get('email', False):
                    email = user.emails.first()
                    if not email:
                        email = user.emails.create(
                            is_main=True, 
                            email_type=UserEmailType.HOME
                        )
                    email.email = f.cleaned_data['email']
                    email.save()
                """

            # print (user)
            # print (f.cleaned_data)
            # print (if_not_false(user.phones.phone_home, 'phone_home'))

            # Check if sub class exist
            if not hasattr(user, 'phones'):
                print ('No phones')
                # Create otherwise
                user.phones = UserPhones.objects.create(
                    user=user
                )

            user.phones.phone_cell = f.cleaned_data['phone_cell']   # if_not_false(user.phones.phone_cell, 'phone_cell')
            user.phones.phone_home = f.cleaned_data['phone_home']   # if_not_false(user.phones.phone_home, 'phone_home')
            user.phones.phone_pro = f.cleaned_data['phone_pro']     # if_not_false(user.phones.phone_pro, 'phone_pro')
            user.phones.save()

            address = user.addresses.first()

            # Check if sub class exist
            if not address:

                # Create otherwise
                address = user.addresses.create(
                    name='',
                    is_main=True, 
                    address_type=UserAddressType.HOME,
                    country='Martinique'
                )
            
            address.address1 = f.cleaned_data['address_1']      # if_not_false(address.address1, 'address_1')
            address.address2 = f.cleaned_data['address_2']      # if_not_false(address.address2, 'address_2')
            address.zip_code = f.cleaned_data['address_zip']    # if_not_false(address.zip_code, 'address_zip')

            if f.cleaned_data['address_zip']:
                address.city = CITIES[address.zip_code]
                # address.city = f.cleaned_data['city']

            address.save()
            
            user.set_slug()
            user.date_completed = _localize(datetime.now())
            user.save()

            transaction.savepoint_commit(sid)
            return user

        except (KeyError, Exception) as e:
            print ('Exception')
            print (e)
            transaction.savepoint_rollback(sid)
            if e.args:
                raise BadRequestException('Invalid payload ({})'.format(str(e.args[0])))
            raise BadRequestException('Invalid payload')
        raise InternalErrorException('End of code reached')

    
    """ Child only  TODO"""
    @staticmethod
    def update_child(user, data):
        """
        Parameters
        ----------
        data {
            dob
            gender
            birthplace
            last_name
            first_name
        }

        Notes
        -----
            Create user
            Add role
            Register sibling
                Create if not exist
            Register family
        """

        f = ChildForm(data)
        if not f.is_valid():
            raise BadRequestException('Le formulaire contient des erreurs.', f.errors)

        sid = transaction.savepoint()
        try:
            user.dob = f.cleaned_data['dob']
            user.gender = f.cleaned_data['gender']
            user.last_name = f.cleaned_data['last_name']
            user.first_name = f.cleaned_data['first_name']
            user.birthplace = f.cleaned_data['birthplace']

            user.date_completed = datetime.now()        
            user.save()

            transaction.savepoint_commit(sid)
            return user

        except KeyError as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                raise BadRequestException('Clé invalide ({}).'.format(str(e.args[0])))
            raise BadRequestException('Clé invalide')

        except Exception as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                raise InternalErrorException('Payload invalide ({})'.format(e.args[0]))
            raise InternalErrorException('Payload invalide')
        
        raise BadRequestException('Une erreur est survenue.')


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
