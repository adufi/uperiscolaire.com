import jwt
import pytz
import json

from datetime import datetime, timedelta

from django.db import transaction
from django.http import QueryDict
from django.conf import settings
from django.core.mail import send_mail
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from users.models import UserAuth, Role, User, UserPhone, UserEmail, UserAddress, UserPhoneType, UserEmailType, UserAddressType, UserPhones
from users.serializers import UserSerializer, UserSerializerShort, EmailSerializer, PhoneSerializer, AddressSerializer, RoleSerializerShort
from users.utils_registers import create_user, create_user_migration

from order.models import Client, ClientCredit, Order, OrderMethod, OrderStatus, Ticket, TicketStatus, StatusEnum, OrderTypeEnum, MethodEnum
from order.serializers import OrderSerializer

from accounting.models import Client as AClient, ClientCreditHistory as AClientCreditHistory, HistoryTypeEnum as HTE

from users.models import User
from params.models import SchoolYear, Product, ProductStock

from registration.models import Sibling, SiblingChild, SiblingIntels, Family, Record, CAF, Health, ChildPAI, ChildClass, ChildQuotient, RecordAuthorizations, RecordDiseases, RecordRecuperater, RecordResponsible
from registration.serializers import RecordSerializer


NAME = 'Paiement ALSH/PERI 2020-2021'
TARIFS_PERI = [20, 32, 40, 60]
PAGINATOR_MAX_PAGE = 25


class NoAuthorizationFound(Exception):
    pass

class InvalidPayloadException(KeyError):
    pass

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
            return _check_authorizations_v2(token, roles)
        except IndexError as e:
            # raise e
            raise 'Aucun token fourni.'
    else:
        raise Exception('No authorization found')


"""
    For testing purpose
"""
def _check_authorizations(token, roles):
    try:
        id = UserAuth.decode_auth_token(token)

        # Invalid id
        if type(id) is str:
            return False
            # return 'Invalid id'

        auth = UserAuth.objects.get(id=id)

        # No user attached to auth - no roles
        if not hasattr(auth, 'user'):
            return False

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

        return False
        # return 'False I don\'t know why'

    except UserAuth.DoesNotExist:
        return False
        # return 'Auth doesnt exist'

    except IndexError:
        return False
        # return 'IndexError'


""" New authorization process with custom exceptions"""
# def check_authorizations_v2(headers, roles):
#     if 'Authorization' in headers:
#         try:
#             token = headers.get('Authorization').split(' ')[1]
#             return _check_authorizations_v2(token, roles)
#         except IndexError as e:
#             raise NoAuthorizationFound('Aucun token fourni.')
#             if e.args:
#                 raise NoAuthorizationFound(e.args[0])
#             raise NoAuthorizationFound('Index error in bearer')
#     else:
#         raise NoAuthorizationFound('No authorization found')


"""
    For testing purpose
"""
# def _check_authorizations_v2(token, roles):
#     try:
#         id = UserAuth.decode_auth_token(token)

#         # Invalid id
#         if type(id) is str:
#             raise UnauthorizedException('Invalid ID')

#         auth = UserAuth.objects.get(id=id)

#         # No user attached to auth - no roles
#         if not hasattr(auth, 'user'):
#             raise UnauthorizedException('No user is bound to auth')

#         # User authenticated
#         if not roles:
#             return {'role': '', 'id': auth.user.id}

#         if 'is_superuser' in roles and auth.is_superuser:
#             return {'role': 'is_superuser', 'id': auth.user.id}

#         _roles = []
#         for role in auth.user.roles.all():
#             if role.slug in roles:
#                 _roles.append(role.slug)
        
#         if _roles:
#             return {'role': ' '.join(_roles), 'id': auth.user.id}

#         raise UnauthorizedException('No role found for this user')

#     except UserAuth.DoesNotExist:
#         raise UnauthorizedException('Auth does not exist')

#     except IndexError:
#         return False
        # return 'IndexError'


"""
check_authorizations(request, []) => basic auth
check_authorizations(request, ['admin', 'is_superuser'])
"""
def check_authorizations_v2(headers, roles):
    if 'Authorization' in headers:
        try:
            token = headers.get('Authorization').split(' ')[1]
        except Exception as e:
            raise UnauthorizedException('Aucun token trouvé')
        return _check_authorizations_v2(token, roles)
    else:
        raise UnauthorizedException('Aucune authorisation trouvée')


"""
    For testing purpose
"""
def _check_authorizations_v2(token, roles):
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

        raise ForbiddenException('Aucun role trouvé pour cet utilisateur')

    except UserAuth.DoesNotExist:
        raise UnauthorizedException('Auth introuvable')

    except IndexError as e:
        print (e.args[0])
        raise UnauthorizedException('Erreur d\'index')



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


class UsersHelper:
    def __init__(self):
        pass

    @staticmethod
    def foo():
        return 'Bar'

    class Auth:

        """ Create an auth from a payload """
        @staticmethod
        @transaction.atomic
        def post(data):
            """
            Parameters
            ----------
            arg => dict {
                email
                password1
                password2
            }

            Returns
            -------
            on error: str
            on success: Auth
            """
            sid = transaction.savepoint()
            try:
                email = data['email']
                password1 = data['password1']
                password2 = data['password2']

                if password1 != password2:
                    return 'Passwords didn\'t matched.'

                if len(password1) < 8:
                    return 'Password too short.'

                auth = UserAuth.objects.filter(email__icontains=email).first()

                if not auth:
                    auth = UserAuth.objects.create_user(
                        email=email,
                        password=password1
                    )
                    # auth.save()
                    transaction.savepoint_commit(sid)
                    return auth
                else:
                    transaction.savepoint_rollback(sid)
                    return 'Email already exist.'
            except:
                transaction.savepoint_rollback(sid)
                return 'Invalid payload.'

        """ Update auth """
        @staticmethod
        def update(data):
            """
            Parameter
            ---------
            arg => dict {
            }

            Returns
            -------
            on error: 
            on success: 
            """
            pass


    class User:

        """ Create an user """
        @staticmethod
        def post(data):
            """
            Parameters
            ----------
            arg1: dict {
                id                  - Optional
                last_name          
                first_name
                online_id           - Optional
                dob                 - Optional - Year-month-day
                is_active           - Optional - default True
                is_auto_password    - Optional - default False
                date_created?       - auto
                date_confirmed?     - auto
                date_completed?     - auto

                roles []            
                    role (slug)     - str
                
                phone               - Optional
                email               - Optional
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

            if 'id' in data:
                id = data['id']
            else:
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
                    online_id=data.get('online_id', 0),
                    is_active=data.get('is_active', True),
                    is_auto_password=data.get('is_auto_password', False)
                )
                # Slug test
                user.set_slug()
                
                if len(User.objects.filter(slug=user.slug)) > 1:
                    raise Exception('Slug already exist')

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
                if 'phone' in data:
                    user.phones.create(
                        phone=data['phone'],
                        is_main=True,
                        phone_type=UserPhoneType.MAIN,
                        user=user
                    )

                # Email
                error = 'Failed to create emails'
                if 'email' in data:

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
                if 'address' in data:
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
            
        
        """ Update an user """
        @staticmethod
        @transaction.atomic
        def update(data):
            """
            Parameters
            ----------
            arg1: dict {
                id
                last_name          
                first_name
                online_id           - Admin   
                dob
                is_active           - Admin - default True
                is_auto_password    - Admin - default False
                
                phone
                email
                address
                    address1
                    address2
                    zip_code
                    city
            }

            Returns
            -------
            """
            # print (data)

            sid = transaction.savepoint()
            try:
                user = User.objects.get(pk=data['id'])

                user.dob = data['dob']
                user.last_name = data['last_name']
                user.first_name = data['first_name']

                user.online_id = data.get('online_id', 0)
                user.is_active = data.get('is_active', True)
                user.is_auto_password = data.get('is_auto_password', False)

                email = user.emails.first()
                if not email:
                    email = user.emails.create(
                        is_main=True, 
                        email_type=UserEmailType.HOME
                    )
                email.email = data['email']
                email.save()

                phone = user.phones.first()
                if not phone:
                    phone = user.phones.create(
                        is_main=True, 
                        phone_type=UserPhoneType.MAIN
                    )
                phone.phone = data['phone']
                phone.save()

                address = user.addresses.first()
                if not address:
                    address = user.addresses.create(
                        name='',
                        is_main=True, 
                        address_type=UserAddressType.HOME,
                        country='Martinique'
                    )
                address.city = data['address']['city']
                address.zip_code = data['address']['zip_code']
                address.address1 = data['address']['address1']
                address.address2 = data['address']['address2']
                address.save()

                user.date_completed = _localize(datetime.now())
                user.save()

                transaction.savepoint_commit(sid)
                return user
            
            except User.DoesNotExist:
                transaction.savepoint_rollback(sid)
                return 'User does not exist'
            except KeyError as e:
                transaction.savepoint_rollback(sid)
                if e.args:
                    return 'Invalid key with error ' + str(e)
                return 'Invalid key'
            except Exception as e:
                transaction.savepoint_rollback(sid)
                if e.args:
                    return 'Invalid payload with error ' + str(e)
                return 'Invalid payload'
            pass
    

    """ Log in an user """
    @staticmethod
    def login():
        pass


    """ Get user status """
    @staticmethod
    def status():
        pass
    
    
    """ User reading """

    @staticmethod
    def user_read(pk):
        _user = UsersHelper._user_read(pk)
        if not _user:
            return False
        return _user


    """ List users - ADMIN """
    @staticmethod
    def users_read(request):
        """ 
        """
        id = request.GET.get('id', 0)
        if id:
            return UsersHelper.user_read(id)
        
        all = User.objects.all()
        filtered = all

        # roles - OR filtering
        # roles = request.GET.get('roles', '').split(',')
        # if roles:
        #     print (roles)
        #     filtered = all.filter(roles__slug__in=roles)
        #     print (filtered)

        # roles - AND filtering
        roles = request.GET.get('roles', '')
        if roles:
            for role in roles.split(','):
                filtered = filtered.filter(roles__slug=role)

        name = request.GET.get('name', '')
        print (name)

        # paginate results
        def processData(data):
            return [x.to_json() for x in data]

        page = int(request.GET.get('page', 1))
        return paginate(filtered, page, processData)


    """ Not used """
    """ Read user profile """
    @staticmethod
    def user_read_(pk):
        user = _user.to_json()
        return user

        # Only ONE phone, email, address 
        phone = _user.phones.first()
        if phone:
            user['phone'] = PhoneSerializer(phone).data['phone']
        
        email = _user.emails.first()
        if email:
            user['email'] = EmailSerializer(email).data['email']

        address = _user.addresses.first()
        if address:
            # user['address'] = {
            #     'city': address.city,
            #     'address1': address.address1,
            #     'address2': address.address2,
            #     'zip_code': address.zip_code,
            # }
            user['address'] = AddressSerializer(address).data

        roles = _user.roles.all()
        if roles:
            user['roles'] = RoleSerializerShort(roles, many=True).data

        return user
    
    """ Not used """
    @staticmethod
    def _user_read(pk):
        try:
            _user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return False
        return _user



    """ User creation """
    """
    Parents
    -------
    register
    migration_parent

    Children
    --------
    create_child
    delete_child
    update_child_sibling
    migration_child --------> TODO

    Common
    ------
    update_user
    user_profile
        child_profile
        parent_profile
    """

    """ Register ONLY a parent """
    @staticmethod
    @transaction.atomic
    def register(data):
        """
        Parameters
        ----------
        arg1: payload - dict {
            email
            password1
            password2
        }
        Return
        ------
        Success -> User
        Failure -> str
        """
        # error = ''

        # Create auth
        auth = UsersHelper.Auth.post(data)

        # Test output
        if type(auth) is str:
            return auth

        sid = transaction.savepoint()
        try:
            # Create user
            # error = 'Failed to create user'
            user = User.objects.create()

            # Add auth to user - Save
            # error = 'Failed to add auth'
            user.auth = auth

            # Create email
            # error = 'Failed to add email'
            user.emails.create(
                is_main=True,
                email=data['email'],
                email_type=UserEmailType.HOME
            )

            # Add role
            # error = 'Failed to add role'
            role = Role.objects.get(slug='parent')
            user.roles.add(role)

            # error = 'Failed to save user'
            user.save()

            # error = 'Failed to serialized'
            transaction.savepoint_commit(sid)
            return user

        except Role.DoesNotExist:
            transaction.savepoint_rollback(sid)
            return 'Role doesn\'t exist.'
            
        except Exception as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                return ('An exception occured with error: ' + e.args[0])


    @staticmethod
    @transaction.atomic
    def migration_parent(data):
        """
        Parameters
        ----------
        arg1: {
            
        }
        Return
        ------
        Success -> User
        Failure -> str
        """
        sid = transaction.savepoint()
        try:
            new_data = {
                'id':           data['id'],
                'first_name':   data['first_name'],
                'last_name':    data['last_name'],
                'email':        data['email'],
                'phone':        data['phone'],
                'address': {
                    'city':         data['address']['city'],
                    'address1':     data['address']['address1'],
                    'address2':     data['address']['address2'],
                    'zip_code':     data['address']['zip_code'],
                },
                'roles': ['parent']
            }
            user = UsersHelper.User.post(new_data)
            if type(user) is str:
                raise Exception(user)

            # error = 'Failed to serialized'
            transaction.savepoint_commit(sid)
            return user

        except KeyError as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                return ('Invalid payload with error: ' + e.args[0])
        except Exception as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                return ('An exception occured with error: ' + e.args[0])


    """ Create a child """
    @staticmethod
    @transaction.atomic
    def create_child(data):
        """
        Parameters
        ----------
        data {
            parent_id

            dob
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
        try:
            new_data = {
                'parent_id':    data['parent_id'],

                'dob':          data['dob'],
                'first_name':   data['first_name'],
                'last_name':    data['last_name'],

                'roles':        ['child']
            }

            # if admin
            # new_data['online_id'] = data.get('online_id', 0)
            # new_data['is_active'] = data.get('is_active', True)
            # new_data['is_auto_password'] = data.get('is_auto_password', False)

        except KeyError as e:
            if e.args:
                return 'Invalid payload ({})'.format(str(e.args[0]))
            return 'Invalid payload'

        except Exception as e:
            if e.args:
                return 'Invalid payload with error: ' + e.args[0]
            return 'Invalid payload'

        sid = transaction.savepoint()

        try:
            user = UsersHelper.User.post(new_data)

            if type(user) is str:
                raise Exception(user)

            # Sibling & Family
            sibling = RegistrationHelper.Sibling.read_by_parent(new_data['parent_id'])
            if not sibling:
                sibling = RegistrationHelper.Sibling.create(new_data['parent_id'])

            if type(sibling) is str:
                raise Exception(sibling)
                
            sibling.add_child(user.id)

            Family.objects.create(
                child=user.id,
                parent=new_data['parent_id']
            )

            transaction.savepoint_commit(sid)
            return user

        except Exception as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                return 'Invalid payload with error: ' + e.args[0]
            return 'Invalid payload'

        return 'An error occured during the process'


    """ """
    @staticmethod
    def delete_child(data):
        """
        Parameters
        ----------
        data {
            child_id
        }
        676
        825
        Notes
        -----
            De-active user
            Remove sibling
            Remove family
        """
        try:
            new_data = {
                'child': data['child']
            }

            user = User.objects.get(pk=new_data['child'])
            user.is_active = False
            user.save()

        except KeyError as e:
            if e.args:
                return 'Invalid payload ({})'.format(str(e.args[0]))
            return 'Invalid payload'

        except User.DoesNotExist:
            return 'User does not exist'

        sibling = RegistrationHelper.Sibling.read_by_child(new_data['child'])
        if sibling:
            sibling.remove_child(new_data['child'])

        family = Family.objects.filter(child=new_data['child'])
        if family:
            family.delete()

        return True


    """ """
    @staticmethod
    def update_child_sibling(data):
        """
        Parameters
        ----------
        {
            child_id
            parent_id
            delete_family   - Default False
        }
        Process
        -------
        Verify data
        Get NEW parent sibling
            Create if none
        Add child to sibling
            Old child sibling will be automatically deleted
        Create a new family
        Delete old one if new parent 
        """
        try:
            new_data = {
                'child_id': data['child_id'],
                'parent_id': data['parent_id'],
                'delete_family': data.get('delete_family', False),
            }

            old = RegistrationHelper.Sibling.read_by_child(new_data['child_id'])

            sibling = RegistrationHelper.Sibling.read_by_parent(new_data['parent_id'])
            if not sibling:
                sibling = RegistrationHelper.Sibling.create(new_data['parent_id'])
            sibling.add_child(new_data['child_id'])

            # Create new family
            if not Family.objects.filter(child=new_data['child_id'], parent=new_data['parent_id']):
                Family.objects.create(child=new_data['child_id'], parent=new_data['parent_id'])

            # Delete old family
            if new_data['delete_family']:
                old_family = Family.objects.filter(child=new_data['child_id'], parent=old.parent)
                if old_family:
                    old_family.delete()

        except (KeyError, Exception) as e:
            if e.args:
                return 'Invalid payload ({})'.format(str(e.args[0]))
            return 'Invalid payload'
    

    """ TODO """
    @staticmethod
    def migration_child(data):
        """
        Parameters
        ----------
        arg1: {
            id
            first_name
            last_name
            online_id
            roles

            family ?
            sibling ?
        }
        Return
        ------
        Success -> User
        Failure -> str
        """
        sid = transaction.savepoint()
        try:
            new_data = {
                'id':           data['id'],
                'first_name':   data['first_name'],
                'last_name':    data['last_name'],
                'online_id':    data.get('online_id', 0),
                'roles':        ['child']
            }
            user = UsersHelper.User.post(new_data)
            if type(user) is str:
                raise Exception(user)

            # error = 'Failed to serialized'
            transaction.savepoint_commit(sid)
            return user

        except KeyError as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                return ('Invalid payload with error: ' + e.args[0])
        except Exception as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                return ('An exception occured with error: ' + e.args[0])



    """ Update an user from user profile """
    @staticmethod
    def update_user(data):
        try:
            new_data = {
                'id':           data['id'],
                'dob':          data['dob'],
                'first_name':   data['first_name'],
                'last_name':    data['last_name'],
                'email':        data['email'],
                'phone':        data['phone'],
                'address': {
                    'city':         data['address']['city'],
                    'address1':     data['address']['address1'],
                    'address2':     data['address']['address2'],
                    'zip_code':     data['address']['zip_code'],
                }
            }

            # if admin
            # new_data['online_id'] = data.get('online_id', 0)
            # new_data['is_active'] = data.get('is_active', True)
            # new_data['is_auto_password'] = data.get('is_auto_password', False)

        except KeyError as e:
            if e.args:
                return ('Invalid payload with error: ' + e.args[0])

        return UsersHelper.User.update(new_data)


class UserHelper:
    # 400
    class BadRequestException(Exception):
        pass

    # 401
    class Unauthorized(Exception):
        pass

    # 402
    class NotFoundException(Exception):
        pass
    
    # 403
    class ForbiddenException(Exception):
        pass

    # 500
    class InternalErrorException(Exception):
        pass

    
    @staticmethod
    def allowed(sibling, pk):
        if pk == sibling.parent:
            return True
        if not sibling.children.filter(child=pk):
            return False
        return True


    @staticmethod
    def read(sibling, pk=0, is_admin=False, GET=None):
        try:
            if not is_admin and not sibling:
                raise UserHelper.InternalErrorException('Sibling is not set')

            if pk:
                # print (is_admin)
                # if is_admin:
                #     return User.objects.get(pk=pk)

                if not is_admin and pk != sibling.parent:
                    # Trigger exception if child is not bound
                    sibling.children.get(child=pk)
                
                return User.objects.get(pk=pk)
            else:
                if is_admin:
                    users = User.objects.all()
                    filtered = users

                    roles = GET.get('roles', '')
                    if roles:
                        for role in roles.split(','):
                            filtered = filtered.filter(roles__slug=role)

                    names = GET.get('names', '')
                    if names:
                        filtered = UserHelper.read_search_name(filtered, names)

                    # paginate results
                    def processData(data):
                        # print (data[0])
                        return [x.to_json() for x in data]

                    page = int(GET.get('page', 1))
                    return paginate(filtered, page, processData)

        except User.DoesNotExist:
            raise UserHelper.NotFoundException('User does not exist')
        except SiblingChild.DoesNotExist:
            pass
        raise UserHelper.ForbiddenException('Vous n\'êtes pas autorisé à consulter cette page.')


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

    
    """ Parent only TODO """
    @staticmethod
    @transaction.atomic
    def register(data):
        """
        Parameters
        ----------
        arg1: payload - dict {
            email
            password1
            password2
        }
        Return
        ------
        Success -> User
        Failure -> str
        """
        # error = ''

        print ('a')
        print ('email: ' + data['email'])

        # Create auth
        auth = UsersHelper.Auth.post(data)

        print ('b1')
        # Test output
        if type(auth) is str:
            return auth

        sid = transaction.savepoint()
        try:
            print ('b2')

            # Create user
            # error = 'Failed to create user'
            try:
                user_id = User.objects.latest('id').id + 1
            except:
                user_id = 1

            user = User.objects.create(id=user_id)

            print ('c')
            # Add auth to user - Save
            # error = 'Failed to add auth'
            user.auth = auth

            # Create email
            # error = 'Failed to add email'
            user.emails.create(
                is_main=True,
                email=data['email'],
                email_type=UserEmailType.HOME
            )
            print ('c')

            user.phones = UserPhones(user=user)
            user.addresses.create(
                is_main=True,
                address_type=UserAddressType.HOME
            )
            print ('d')

            # Add role
            # error = 'Failed to add role'
            role = Role.objects.get(slug='parent')
            user.roles.add(role)

            print ('e')

            # error = 'Failed to save user'
            user.save()

            print ('f')

            Sibling.objects.create(parent=user.id)

            print ('g')

            # UserHelper.register_send_mail(user.id, data['email'])

            # error = 'Failed to serialized'
            transaction.savepoint_commit(sid)
            return user

        except Role.DoesNotExist:
            transaction.savepoint_rollback(sid)
            return 'Role doesn\'t exist.'
            
        except Exception as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                return ('An exception occured with error: ' + e.args[0])


    @staticmethod
    def register_send_mail(host, id, email):
        token = UserHelper._encode_activation_token(id)
        message = '''Bonjour,

        Pour finaliser votre inscription au nouveau service en ligne de L'U.P.E.M., veuillez confirmer votre adresse email en cliquant sur le lien suivant:

        http://{}/verify/{}/

        Service Périscolaire de l'UPEEM.

        (*) Ce lien d'activation n'est valable que pour une durée de 7 jours.'''.format(host, token)
        try:
            send_mail(
                'Activation de votre compte',
                message,
                'UPEEM (Ne pas répondre) <noreply@upem.online>',
                [email]
            )
        except Exception as e:
            print ('register_send_mail() An exception occured with error: ' + str(e))

    
    @staticmethod
    def change_password(host, id, email):
        token = UserHelper._encode_change_password_token(id)
        message = '''Bonjour,

        Cliquez sur ce lien pour réinitialiser votre mot de passe pour le compte "email".

        Lien: http://{}/change-password/{}/

        Si vous n'avez pas demandé à réinitialiser votre mot de passe, vous pouvez ignorer cet email.

        Service Périscolaire de l'UPEEM.

        (*) Ce lien de réinitialisation n'est valable que pour une durée de 24h.'''.format(host, token)
        send_mail(
            'Changement de mot de passe',
            message,
            'UPEEM (Ne pas répondre) <noreply@upem.online>',
            [email]
        )


    """ Child only  TODO"""
    @staticmethod
    def create(sibling, data, is_admin):
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
        if not sibling and not is_admin:
            raise UserHelper.InternalErrorException('Sibling is not set')

        sid = transaction.savepoint()
        try:
            new_data = {
                'dob':          data['dob'],
                'first_name':   data['first_name'],
                'last_name':    data['last_name'],
                'gender':       data['gender'],
                'birthplace':   data['birthplace'],

                'roles':        ['child']
            }

            # error = False
            # error_msg = ''

            # if not data['dob']:
            #     error = True
            #     error_msg = ''

            # if not data['first_name']:
            #     error = True
            #     error_msg = ''

            # if not data['last_name']:
            #     error = True
            #     error_msg = ''

            # if not data['gender']:
            #     error = True
            #     error_msg = ''

            # if not data['birthplace']:
            #     error = True
            #     error_msg = ''

            test = [
                not data['dob'],
                not data['first_name'],
                not data['last_name'],
                not data['gender'],
                # not data['birthplace'],
            ]

            if any(test):
                raise UserHelper.BadRequestException('Every fields must be set')

            if is_admin:
                sibling = Sibling.objects.get(parent=data['parent_id'])

                id = data.get('id', 0)

                if 'email' in data :
                    new_data['email'] = data['email']
                if 'phone' in data :
                    new_data['phone'] = data['phone']
                if 'address' in data :
                    new_data['address'] = data['address']

                new_data['online_id'] = data.get('online_id', 0)
                new_data['is_active'] = data.get('is_active', True)
                new_data['is_auto_password'] = data.get('is_auto_password', False)
            else:
                id = 0

            user = UserHelper._create(new_data, id)

            if type(user) is str:
                raise Exception(user)

            user.date_completed = datetime.now()        
            user.save()

            # Sibling & Family
            # sibling = RegistrationHelper.Sibling.read_by_parent(new_data['parent_id'])
            # if not sibling:
            #     sibling = RegistrationHelper.Sibling.create(new_data['parent_id'])

            # if type(sibling) is str:
            #     raise Exception(sibling)
                
            sibling.add_child(user.id)

            Family.objects.create(
                child=user.id,
                parent=sibling.parent
            )

            transaction.savepoint_commit(sid)
            return user

        except KeyError as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                raise UserHelper.BadRequestException('Invalid payload. Error on key ({})'.format(str(e.args[0])))
            raise UserHelper.BadRequestException('Invalid payload')

        except Exception as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                raise UserHelper.InternalErrorException('Invalid payload ({})'.format(e.args[0]))
            raise UserHelper.InternalErrorException('Invalid payload')


    """ TODO """
    @staticmethod
    @transaction.atomic
    def _create(data, id=0):
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
        if not is_admin:
            if not sibling:
                raise UserHelper.InternalErrorException('Sibling is not set')

            if not UserHelper.allowed(sibling, pk):
                raise UserHelper.ForbiddenException('Vous n\'êtes pas autorisé à consulter cette page.')

        try:
            user = User.objects.get(pk=pk)
            return UserHelper._update(user, data, is_admin)
        
        except User.DoesNotExist:
            pass

    
    @staticmethod
    @transaction.atomic
    def _update(user, data, is_admin):
        sid = transaction.savepoint()
        try:
            slug = set_slug(data['last_name'] + data['first_name'])

            if User.objects.filter(slug=slug).exclude(id=user.id):
                raise UserHelper.BadRequestException('Slug already exist')

            user.gender = data['gender']
            user.last_name = data['last_name']
            user.first_name = data['first_name']

            # Optional
            user.job = data.get('job', '')
            user.dob = data.get('dob', None)
            user.birthplace = data.get('birthplace', '')
            user.accept_newsletter = data.get('accept_newsletter', False)

            if is_admin:
                user.id = data.get('id', user.id)
                user.online_id = data.get('online_id', user.online_id)

                user.date_created = data.get('date_created', user.date_created)
                user.date_confirmed = data.get('date_confirmed', user.date_confirmed)
                user.date_completed = data.get('date_completed', user.date_completed)

                user.is_active = data.get('is_active', user.is_active)
                user.is_auto_password = data.get('is_auto_password', user.is_auto_password)

            if user.roles.filter(slug='parent'):
                
                if data.get('email', False):
                    email = user.emails.first()
                    if not email:
                        email = user.emails.create(
                            is_main=True, 
                            email_type=UserEmailType.HOME
                        )
                    email.email = data['email']
                    email.save()

                if data.get('phones', False):
                    if not hasattr(user, 'phones'):
                        user.phones = UserPhones.objects.create(
                            user=user
                        )
                    user.phones.phone_cell = data['phones']['cell']
                    user.phones.phone_home = data['phones']['home']
                    user.phones.phone_pro = data['phones']['pro']
                    user.phones.save()

                if data.get('address', False):
                    address = user.addresses.first()
                    if not address:
                        address = user.addresses.create(
                            name='',
                            is_main=True, 
                            address_type=UserAddressType.HOME,
                            country='Martinique'
                        )
                    address.city        = data['address']['city']
                    address.zip_code    = data['address']['zip_code']
                    address.address1    = data['address']['address1']
                    address.address2    = data['address']['address2']
                    address.save()
            
            user.set_slug()
            user.date_completed = _localize(datetime.now())
            user.save()

            # print (user.id)
            print (is_admin)
            print (data)
            
            # Exceptionaly credit
            if is_admin and 'credit' in data:
                print ('1')
                try:
                    client = Client.objects.get(
                        user=user.id
                    )
                    print ('Found')
                except Client.DoesNotExist:
                    client = Client.objects.create(
                        id=user.id,
                        user=user.id,
                    )
                    client.credit = ClientCredit.objects.create(client=client)
                    print ('Created')
                finally:
                    client.credit.set(data['credit'])

            transaction.savepoint_commit(sid)
            return user

        except (KeyError, Exception) as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                raise IntelHelper.BadRequestException('Invalid payload ({})'.format(str(e.args[0])))
            raise IntelHelper.BadRequestException('Invalid payload')
        raise UserHelper.InternalErrorException('End of code reached')

    
    @staticmethod
    def _encode_activation_token(id):
        """Generates the auth token"""
        try:
            payload = {
                'exp':
                    datetime.utcnow() + timedelta(
                        days=settings.EMAIL_VERIFICATION_EXPIRATION_DAYS,
                        seconds=settings.EMAIL_VERIFICATION_EXPIRATION_SECONDS
                    ),
                # 'iat': datetime.utcnow(),
                'id': id,
                'type': 'email_activation'
            }
            token = jwt.encode(
                payload,
                settings.SECRET_KEY,
                algorithm='HS256'
            )
            return token.decode('utf-8')
        except Exception as e:
            return e


    @staticmethod
    def _decode_activation_token(auth_token):
        """
        Decodes the auth token - :param auth_token: - :return: integer|string
        """
        try:
            payload = jwt.decode(
                auth_token, 
                settings.SECRET_KEY
            )
            payload_type = payload.get('type', False)
            if not payload_type or payload_type != 'email_activation':
                return 'Invalid payload type.'
            return payload['id']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'


    @staticmethod
    def _encode_change_password_token(id):
        """Generates the auth token"""
        try:
            payload = {
                'exp':
                    datetime.utcnow() + timedelta(
                        days=settings.PASSWORD_CHANGE_EXPIRATION_DAYS,
                        seconds=settings.PASSWORD_CHANGE_EXPIRATION_SECONDS
                    ),
                # 'iat': datetime.utcnow(),
                'id': id,
                'type': 'change_password'
            }
            token = jwt.encode(
                payload,
                settings.SECRET_KEY,
                algorithm='HS256'
            )
            return token.decode('utf-8')
        except Exception as e:
            return e


    @staticmethod
    def _decode_change_password_token(auth_token):
        """
        Decodes the auth token - :param auth_token: - :return: integer|string
        """
        try:
            payload = jwt.decode(
                auth_token, 
                settings.SECRET_KEY
            )
            payload_type = payload.get('type', False)
            if not payload_type or payload_type != 'change_password':
                return 'Invalid payload type.'
            return payload['id']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'


class SiblingHelper:
    # 400
    class BadRequestException(Exception):
        pass

    # 401
    class Unauthorized(Exception):
        pass

    # 402
    class NotFoundException(Exception):
        pass
    
    # 403
    class ForbiddenException(Exception):
        pass

    # 500
    class InternalErrorException(Exception):
        pass

    
    @staticmethod
    def allowed(sibling, pk):
        if pk == sibling.parent:
            return True
        if not sibling.children.filter(child=pk):
            return False
        return True


    @staticmethod
    def read(sibling, pk=0, is_admin=False, GET=None):
        try:
            if pk:
                if is_admin:
                    return Sibling.objects.get(pk=pk)
                
                if not sibling:
                    raise UserHelper.InternalErrorException('Sibling is not set')
                
                return sibling

            else:
                parent_id = GET.get('parent', 0)
                child_id = GET.get('child', 0)

                # if parent_id == sibling.id:
                #     return sibling

                filtered = None
                siblings = None

                if parent_id:
                    filtered = Sibling.objects.get(parent=parent_id)

                elif child_id:
                    filtered = Sibling.objects.get(children__child=child_id)

                else:
                    siblings = Sibling.objects.all()

                if is_admin:
                    return filtered if filtered else siblings

                if filtered and sibling.id == filtered.id:
                    return filtered
                
                raise SiblingHelper.ForbiddenException('Vous n\'êtes pas autorisé à consulter cette page.')

        except Sibling.DoesNotExist:
            raise SiblingHelper.NotFoundException('Sibling does not exist')
        except SiblingChild.DoesNotExist:
            pass
        raise SiblingHelper.ForbiddenException('Vous n\'êtes pas autorisé à consulter cette page.')

    
    @staticmethod
    def update(sibling, pk, data, is_admin=False):
        """
        Parameters
        ----------
        data {

        }
        """
        if not is_admin:
            if not sibling:
                raise UserHelper.InternalErrorException('Sibling is not set')

            if not UserHelper.allowed(sibling, pk):
                raise UserHelper.ForbiddenException('Vous n\'êtes pas autorisé à consulter cette page.')

        try:
            user = User.objects.get(pk=pk)
            return UserHelper._update(user, data, is_admin)
        
        except User.DoesNotExist:
            pass

    
    @staticmethod
    @transaction.atomic
    def _update(user, data, is_admin):
        sid = transaction.savepoint()
        try:
            slug = set_slug(data['last_name'] + data['first_name'])

            if User.objects.filter(slug=slug).exclude(id=user.id):
                raise UserHelper.BadRequestException('Slug already exist')


            user.dob = data['dob']
            user.last_name = data['last_name']
            user.first_name = data['first_name']

            if is_admin:
                user.id = data.get('id', user.id)
                user.online_id = data.get('online_id', user.online_id)

                user.is_active = data.get('is_active', user.is_active)
                user.is_auto_password = data.get('is_auto_password', user.is_auto_password)

            if user.roles.filter(slug='parent'):
                email = user.emails.first()
                if not email:
                    email = user.emails.create(
                        is_main=True, 
                        email_type=UserEmailType.HOME
                    )
                email.email = data['email']
                email.save()

                phone = user.phones.first()
                if not phone:
                    phone = user.phones.create(
                        is_main=True, 
                        phone_type=UserPhoneType.MAIN
                    )
                phone.phone = data['phone']
                phone.save()

                address = user.addresses.first()
                if not address:
                    address = user.addresses.create(
                        name='',
                        is_main=True, 
                        address_type=UserAddressType.HOME,
                        country='Martinique'
                    )
                address.city        = data['address']['city']
                address.zip_code    = data['address']['zip_code']
                address.address1    = data['address']['address1']
                address.address2    = data['address']['address2']
                address.save()
            
            user.set_slug()
            user.date_completed = _localize(datetime.now())
            user.save()

            transaction.savepoint_commit(sid)
            return user

        except (KeyError, Exception) as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                raise IntelHelper.BadRequestException('Invalid payload ({})'.format(str(e.args[0])))
            raise IntelHelper.BadRequestException('Invalid payload')
        raise UserHelper.InternalErrorException('End of code reached')


class IntelHelper:
    # 400
    class BadRequestException(Exception):
        pass

    # 401
    class Unauthorized(Exception):
        pass

    # 402
    class NotFoundException(Exception):
        pass
    
    # 403
    class ForbiddenException(Exception):
        pass

    # 500
    class InternalErrorException(Exception):
        pass


    class SiblingNotSet(Exception):
        pass
   

    @staticmethod
    def read(sibling, pk=0, is_admin=False, GET=None):
        try:
            if pk:
                if is_admin:
                    return SiblingIntels.objects.get(pk=pk)

                if not sibling:
                    raise IntelHelper.InternalErrorException('Sibling is not set')
                
                return sibling.intels.get(pk=pk)

            else:
                if is_admin and GET:
                    all = GET.get('all', False)
                    if all:
                        return SiblingIntels.objects.all()
                    parent_id = GET.get('parent', 0)
                    if parent_id:
                        return SiblingIntels.objects.filter(sibling__parent=parent_id)

                if not sibling:
                    raise IntelHelper.InternalErrorException('Sibling is not set')

                return sibling.intels.all()
                
            raise IntelHelper.InternalErrorException('End of code reached.')        
        except SiblingIntels.DoesNotExist:
            raise IntelHelper.NotFoundException('Intel not found.')


    @staticmethod
    def create(sibling, data, is_admin=False):
        """
        Parameters
        ----------
        data {
            parent_id           - Admin
            quotient_1          - Admin
            quotient_2          - Admin

            recipent_number

            school_year         - Auto/admin

            date_created        - Auto/admin 
            date_verified       - Auto/admin
            date_last_mod       - Auto/admin
        }
        """
        try:
            if not sibling:
                raise IntelHelper.InternalErrorException('Sibling is not set')
                
            school_year = 0

            new_data = {
                'recipent_number':  data.get('recipent_number', 0),
                # 'insurance_policy': data.get('insurance_policy', 0),  
                # 'insurance_society': data.get('insurance_society', '')    
            }

            if is_admin:
                new_data['quotient_1'] = data.get('quotient_1', ChildQuotient.UNSET)
                new_data['quotient_2'] = data.get('quotient_2', ChildQuotient.UNSET)
                school_year = data.get('school_year', 0)

            if not school_year:
                _ = SchoolYear.objects.get(is_active=True)
                school_year = _.id

            intel = sibling.add_intels(new_data, school_year)  
            if not intel:
                raise IntelHelper.ForbiddenException('Intel already exist')  
                # raise IntelHelper.BadRequestException('Intel already exist')  

            if intel and is_admin and new_data.get('verified', False):
                intel.date_verified = datetime.now()
                intel.save()

            return intel
        
        except SchoolYear.DoesNotExist:
            raise SchoolYear.DoesNotExist
        
        except (KeyError, Exception) as e:
            if e.args:
                raise IntelHelper.BadRequestException('Invalid payload ({})'.format(str(e.args[0])))
            raise IntelHelper.BadRequestException('Invalid payload')

    @staticmethod
    def update(sibling, data, pk=0, is_admin=False):
        """
        NOTE
        ----
        As parent
            pk      - Update if active
            no pk   - Update active (if sibling)
        As admin
            pk      - Update
            no pk   - Update active (if sibling)

        Parameters
        ----------
        data {
            quotient_1          - Admin
            quotient_2          - Admin

            recipent_number 

            school_year         - Auto or admin

            date_created
            date_verified
            date_last_mod
        }
        """
        try:
            active = SchoolYear.objects.get(is_active=True)

            # Update active intel
            if pk == 0:

                # Check sibling
                if not sibling:
                    raise IntelHelper.InternalErrorException('Sibling is not set')

                # Check active sibling
                intel = sibling.intels.get(school_year=active.id)

                intel = IntelHelper._update_intel(intel, data, is_admin)

            # Update requested intel
            else:
                intel = SiblingIntels.objects.get(pk=pk)

                # Re-route non admin
                if not is_admin:

                    # Check active intel
                    if intel.school_year != active.id:
                        raise IntelHelper.ForbiddenException('Inscription fermée à cette période.')

                    # Check own intel
                    if not sibling.intels.filter(pk=pk):
                        raise IntelHelper.ForbiddenException('Vous n\'êtes pas autorisé à accéder à cette ressource.')
                        
                    return IntelHelper.update(sibling, data)

                intel = IntelHelper._update_intel(intel, data, is_admin)

            return intel

        except SchoolYear.DoesNotExist:
            raise IntelHelper.ForbiddenException('Inscription fermée à cette période.')

        except SchoolYear.MultipleObjectsReturned:
            raise IntelHelper.InternalErrorException('Multiple objets année scolaire.')

        except SiblingIntels.DoesNotExist:
            raise IntelHelper.NotFoundException('Information introuvable.')

        except SiblingIntels.MultipleObjectsReturned:
            raise IntelHelper.InternalErrorException('Multiple objets inscription.')
        
        except (KeyError, Exception) as e:
            if e.args:
                raise IntelHelper.BadRequestException('Invalid payload ({})'.format(str(e.args[0])))
            raise IntelHelper.BadRequestException('Invalid payload')


    @staticmethod
    def _update_intel(intel, data, is_admin=False):
        intel.recipent_number = data.get('recipent_number', 0)
        # intel.insurance_policy = data.get('insurance_policy', 0)
        # intel.insurance_society = data.get('insurance_society', '')
        
        if is_admin:
            intel.quotient_1 = data.get('quotient_1', intel.quotient_1)
            intel.quotient_2 = data.get('quotient_2', intel.quotient_2)
            intel.school_year = data.get('school_year', intel.school_year)
            intel.date_created = data.get('date_created', intel.date_created)

            intel.date_verified = datetime.now()

        intel.date_last_mod = datetime.now()
        intel.save()
        return intel


class RecordHelper:
    # 400
    class BadRequestException(Exception):
        pass

    # 401
    class Unauthorized(Exception):
        pass

    # 402
    class NotFoundException(Exception):
        pass
    
    # 403
    class ForbiddenException(Exception):
        pass

    # 500
    class InternalErrorException(Exception):
        pass

    
    @staticmethod
    def allowed(sibling, child):
        if not sibling.children.filter(child=child):
            return False
        return True


    @staticmethod
    def read(sibling, pk=0, is_admin=False, GET=None):
        try:
            if not is_admin and not sibling:
                raise InternalErrorException('Sibling is not set')

            if pk:
                record = Record.objects.get(pk=pk)
                if not is_admin and not RecordHelper.allowed(sibling, record.child):
                    raise ForbiddenException('Vous n\'êtes pas autorisé à consulter cette page.')
                return record
            
            else:
                child_id = GET.get('child', 0)
                parent_id = GET.get('parent', 0)

                if is_admin:
                    if parent_id:
                        children = SiblingChild.objects.filter(sibling__parent=parent_id)
                        return Record.objects.filter(child__in=[child.child for child in children])

                    if child_id:
                        return Record.objects.filter(child=child_id)

                    return Record.objects.all()

                else:
                    if parent_id:
                        if int(parent_id) == sibling.parent:
                            children = sibling.children.all()
                            return Record.objects.filter(child__in=[child.child for child in children])

                    if child_id:
                        if RecordHelper.allowed(sibling, child_id):
                            return Record.objects.filter(child=child_id)

                raise ForbiddenException('Vous n\'êtes pas autorisé à consulter cette page.')

        except Record.DoesNotExist:
            raise NotFoundException('Record does not exist')

        raise ForbiddenException('Vous n\'êtes pas autorisé à consulter cette page.')


    @staticmethod
    @transaction.atomic
    def create(sibling, data, is_admin):
        """
        Parameters
        ----------
        data {
            child_id
            parent_id
            school_year

            school
            classroom
            agreement

            accueil_mati
            accueil_midi
            accueil_merc
            accueil_vacs

            insurance_policy
            insurance_society

            date_created
            date_last_mod
            date_verified

            health
                asthme
                lunettes
                lentilles
                medical_treatment
                vaccine_up_to_date
                protheses_dentaire
                protheses_auditives

                pai
                allergy_food
                allergy_drug
                pai_details
                allergy_food_details
                allergy_drug_details

                autres_recommendations

                doctor_names
                doctor_phones

            diseases
                rubeole
                varicelle
                angine
                rhumatisme
                scarlatine
                coqueluche
                otite
                rougeole
                oreillons

            responsible         - Parent 2 - Only one is needed
                last_name
                first_name
                job
                gender
                email
                phone_cell
                phone_home
                phone_pro
                address_zip
                address_city
                address_address1
                address_address2

            recuperaters [{
                names
                phones
                quality
            }]

            authorizations
                bath
                image
                sport
                transport
                medical_transport
        }

        NOTE
        -----
            
        """
        if not sibling and not is_admin:
            raise InternalErrorException('Sibling is not set')

        sid = transaction.savepoint()

        # Data checking
        if not data['child_id']:
            raise BadRequestException('ID enfant non définie.')

        if not any([
                data['accueil_mati'],
                data['accueil_midi'],
                data['accueil_merc'],
                data['accueil_vacs']
            ]):
            raise BadRequestException ('Aucun type accueil choisi.')

        if not data['agreement']:
            raise BadRequestException ('Veuillez consentir au formulaire.')

        try:
            id = Record.objects.latest('id').id + 1
        except:
            id = 1

        try:
            school_year = SchoolYear.objects.get(is_active=True).id

            if not is_admin: 
                if not RecordHelper.allowed(sibling, data['child_id']):
                    raise ForbiddenException()
                
                date_verified = None
            else:
                if data['school_year']:
                    school_year = data['school_year']
                date_verified = datetime.now()

            if Record.objects.filter(child=data['child_id'], school_year=school_year):
                raise BadRequestException('Inscription déjà existante.')

            record = Record.objects.create(
                id=id,
                child=data['child_id'],
                school=data['school'],
                agreement=data['agreement'],
                classroom=data['classroom'],
                accueil_mati=data['accueil_mati'],
                accueil_midi=data['accueil_midi'],
                accueil_merc=data['accueil_merc'],
                accueil_vacs=data['accueil_vacs'],
                insurance_policy=data['insurance_policy'],
                insurance_society=data['insurance_society'],
                school_year=school_year,
                date_verified=date_verified
            )
            
            health = data['health']
            Health.objects.create(
                asthme=health['asthme'],
                lentilles=health['lentilles'],
                lunettes=health['lunettes'],
                medical_treatment=health['medical_treatment'],
                vaccine_up_to_date=health['vaccine_up_to_date'],
                protheses_dentaire=health['protheses_dentaire'],
                protheses_auditives=health['protheses_auditives'],

                doctor_names=health['doctor_names'],
                doctor_phones=health['doctor_phones'],

                autres_recommandations=health['autres_recommandations'],

                pai=health['pai'],
                pai_details=health['pai_details'],
                allergy_food=health['allergy_food'],
                allergy_drug=health['allergy_drug'],
                allergy_food_details=health['allergy_food_details'],
                allergy_drug_details=health['allergy_drug_details'],
                record=record
            )

            diseases = data['diseases']
            RecordDiseases.objects.create(
                rubeole=diseases['rubeole'],
                varicelle=diseases['varicelle'],
                angine=diseases['angine'],
                rhumatisme=diseases['rhumatisme'],
                scarlatine=diseases['scarlatine'],
                coqueluche=diseases['coqueluche'],
                otite=diseases['otite'],
                rougeole=diseases['rougeole'],
                oreillons=diseases['oreillons'],

                record=record
            )

            responsible = data['responsible']
            record.responsibles.create(
                job=responsible['job'],
                gender=responsible['gender'],
                last_name=responsible['last_name'],
                first_name=responsible['first_name'],

                email=responsible['email'],
                
                phone_cell=responsible['phone_cell'],
                phone_home=responsible['phone_home'],
                phone_pro=responsible['phone_pro'],

                address_zip=responsible['address_zip'],
                address_city=responsible['address_city'],
                address_address1=responsible['address_address1'],
                address_address2=responsible['address_address2'],

                record=record
            )

            # print (data['recuperaters'])
            for recuperater in data['recuperaters']:
                if recuperater['names'] and recuperater['phones']:
                    RecordRecuperater.objects.create(
                        names=recuperater['names'],
                        phones=recuperater['phones'],
                        quality=recuperater['quality'],
                        record=record
                    )

            authorizations = data['authorizations']
            RecordAuthorizations.objects.create(
                bath=authorizations['bath'],
                image=authorizations['image'],
                sport=authorizations['sport'],
                transport=authorizations['transport'],
                medical_transport=authorizations['medical_transport'],

                record=record
            )

            transaction.savepoint_commit(sid)
            return record

        except SchoolYear.DoesNotExist:
            raise NotFoundException('Aucune année scolaire active.')

        except BadRequestException as e:
            raise BadRequestException(e.args[0])

        except KeyError as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                raise BadRequestException('Invalid payload. Error on key ({})'.format(str(e.args[0])))
            raise BadRequestException('Invalid payload')

        except Exception as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                raise InternalErrorException('Invalid payload ({})'.format(e.args[0]))
            raise InternalErrorException('Invalid payload')


    @staticmethod
    def update(sibling, pk, data, is_admin=False):
        """
        Parameters
        ----------
        data {
            id
            child_id
            parent_id
            school_year

            school
            classroom
            agreement

            accueil_mati
            accueil_midi
            accueil_merc
            accueil_vacs

            insurance_policy
            insurance_society

            date_created
            date_last_mod
            date_verified

            health
                asthme
                lunettes
                lentilles
                medical_treatment
                vaccine_up_to_date
                protheses_dentaire
                protheses_auditives

                pai
                allergy_food
                allergy_drug
                pai_details
                allergy_food_details
                allergy_drug_details

                autres_recommendations

                doctor_names
                doctor_phones

            diseases
                rubeole
                varicelle
                angine
                rhumatisme
                scarlatine
                coqueluche
                otite
                rougeole
                oreillons

            responsible         - Parent 2 - Only one is needed
                last_name
                first_name
                job
                gender
                email
                phone_cell
                phone_home
                phone_pro
                address_zip
                address_city
                address_address1
                address_address2

            recuperaters [{
                names
                phones
            }]

            authorizations
                bath
                image
                sport
                transport
                medical_transport
        }

        NOTE
        ----
            
        """
        if not sibling and not is_admin:
            raise InternalErrorException('Sibling is not set')

        # Data checking
        if not data['child_id']:
            raise BadRequestException('ID enfant non définie.')

        if not any([
                data['accueil_mati'],
                data['accueil_midi'],
                data['accueil_merc'],
                data['accueil_vacs']
            ]):
            raise BadRequestException ('Aucun type accueil choisi.')

        if not data['agreement']:
            raise BadRequestException ('Veuillez consentir au formulaire.')

        sid = transaction.savepoint()

        try:
            school_year = SchoolYear.objects.get(is_active=True).id

            record = Record.objects.get(pk=pk)

            # As parent raise error
            # if record verified
            # if record not active (SY)
            # if child is not bound to parent
            if not is_admin: 
                if not RecordHelper.allowed(sibling, record.child):
                    raise ForbiddenException()
                    
                if record.school_year != school_year:
                    raise ForbiddenException()

                if record.date_verified:
                    raise ForbiddenException()
            
            # Update record            
            record.child = data['child_id']
            record.school = data['school']
            record.agreement = data['agreement']
            record.classroom = data['classroom']
            record.accueil_mati = data['accueil_mati']
            record.accueil_midi = data['accueil_midi']
            record.accueil_merc = data['accueil_merc']
            record.accueil_vacs = data['accueil_vacs']
            record.insurance_policy = data['insurance_policy']
            record.insurance_society = data['insurance_society']
            
            
            health = data['health']

            record.health.asthme               = health['asthme']
            record.health.lentilles            = health['lentilles']
            record.health.lunettes             = health['lunettes']
            record.health.medical_treatment    = health['medical_treatment']
            record.health.vaccine_up_to_date   = health['vaccine_up_to_date']
            record.health.protheses_dentaire   = health['protheses_dentaire']
            record.health.protheses_auditives  = health['protheses_auditives']

            record.health.doctor_names         = health['doctor_names']
            record.health.doctor_phones        = health['doctor_phones']

            record.health.autres_recommandations = health['autres_recommandations']

            record.health.pai                  = health['pai']
            record.health.pai_details          = health['pai_details']
            record.health.allergy_food         = health['allergy_food']
            record.health.allergy_drug         = health['allergy_drug']
            record.health.allergy_food_details = health['allergy_food_details']
            record.health.allergy_drug_details = health['allergy_drug_details']
            record.health.save()


            diseases = data['diseases']
            record.diseases.rubeole     = diseases['rubeole']
            record.diseases.varicelle   = diseases['varicelle']
            record.diseases.angine      = diseases['angine']
            record.diseases.rhumatisme  = diseases['rhumatisme']
            record.diseases.scarlatine  = diseases['scarlatine']
            record.diseases.coqueluche  = diseases['coqueluche']
            record.diseases.otite       = diseases['otite']
            record.diseases.rougeole    = diseases['rougeole']
            record.diseases.oreillons   = diseases['oreillons']
            record.diseases.save()
            

            responsible = data['responsible']
            _responsible = record.responsibles.first()
            _responsible.job = responsible['job']
            _responsible.gender = responsible['gender']
            _responsible.last_name = responsible['last_name']
            _responsible.first_name = responsible['first_name']

            _responsible.email = responsible['email']
                
            _responsible.phone_cell = responsible['phone_cell']
            _responsible.phone_home = responsible['phone_home']
            _responsible.phone_pro = responsible['phone_pro']

            _responsible.address_zip = responsible['address_zip']
            _responsible.address_city = responsible['address_city']
            _responsible.address_address1 = responsible['address_address1']
            _responsible.address_address2 = responsible['address_address2']
            _responsible.save()

            _recuperaters = record.recuperaters.all()
            for i, recuperater in enumerate(data['recuperaters']):
                if recuperater['names'] and recuperater['phones'] and recuperater['quality']:
                    try:
                        _recuperater = _recuperaters[i]
                    except:
                        _recuperater = RecordRecuperater.objects.create(record=record)

                    _recuperater.names = recuperater['names']
                    _recuperater.phones = recuperater['phones']
                    _recuperater.quality = recuperater['quality']
                    _recuperater.save()


            authorizations = data['authorizations']
            record.authorizations.bath = authorizations['bath']
            record.authorizations.image = authorizations['image']
            record.authorizations.sport = authorizations['sport']
            record.authorizations.transport = authorizations['transport']
            record.authorizations.medical_transport = authorizations['medical_transport']
            record.authorizations.save()

            if is_admin:
                record.id = data.get('id', record.id)
                record.child = data.get('child', record.child)
                record.school_year = data.get('school_year', record.school_year)

                record.date_created = data.get('date_created', record.date_created)
                record.date_verified = data.get('date_verified', record.date_verified)

            record.date_last_mod = datetime.now()
            record.save()

            transaction.savepoint_commit(sid)
            return record

        except SchoolYear.DoesNotExist:
            raise NotFoundException('Aucune année scolaire active.')

        except BadRequestException as e:
            raise BadRequestException(e.args[0])

        except KeyError as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                raise BadRequestException('Invalid payload. Error on key ({})'.format(str(e.args[0])))
            raise BadRequestException('Invalid payload. Key error.')

        except Exception as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                raise InternalErrorException('Invalid payload ({})'.format(e.args[0]))
            raise InternalErrorException('Invalid payload')


class RegistrationHelper:
    
    class Child:

        @staticmethod
        def get(pk):
            try:
                return Child.objects.get(pk=pk)
            except:
                return None

        @staticmethod
        def get_from_user(user):
            try:
                return Child.objects.get(user=user)
            except:
                return None
        
        """ Create a child """
        @staticmethod
        @transaction.atomic
        def create(id):
            sid = transaction.savepoint()
            try:
                child = Child.objects.create(
                    id=id,
                    user=id
                )
                transaction.savepoint_commit(sid)
                return child
            except:
                transaction.savepoint_rollback(sid)
                return 'An error occurred during the transaction.'

        """ Update a child """
        @staticmethod
        @transaction.atomic
        def update(data):
            sid = transaction.savepoint()
            try:
                child = Child.objects.get(user=data['id'])
                child.user = data['user']
                transaction.savepoint_commit(sid)
                return child
            except Child.DoesNotExist:
                transaction.savepoint_rollback(sid)
                return 'Child does not exist.'
            except:
                transaction.savepoint_rollback(sid)
                return 'An error occurred during the transaction.'

        @staticmethod
        def delete(pk):
            Child.objects.filter(pk=pk).delete()

        @staticmethod
        def delete_from_user(user):
            Child.objects.filter(user=user).delete()

    class Record:
    
        """ Create a record """
        @staticmethod
        @transaction.atomic
        def create(child, data):
            """
            Parameters
            ----------
            arg: dict {
                id
                school
                classroom
                date_created
                date_verified   - blank
                date_last_mod   - blank
                caf
                    q1
                    q2
                    recipent_number
                health
                    asthme
                    allergy_food 
                    allergy_drug 
                    allergy_food_details
                    allergy_drug_details
                    pai
            """
            sid = transaction.savepoint()

            try:
                id = data['id']
            except KeyError:
                id = User.objects.latest('id').id + 1
            except:
                id = 1

            try:
                flag = 'Record object'
                r = Record.objects.create(
                    id=id,
                    school=data['school'],
                    classroom=data['classroom'],
                    child=child,
                )

                """ CAF Handle """
                flag = 'CAF object'

                c = CAF.objects.create(
                    q1=data['caf']['q1'],
                    q2=data['caf']['q2'],
                    recipent_number=data['caf']['recipent_number'],
                    record=r
                )

                """ Health Handle """
                flag = 'Health object'
                health = data['health']
                h = Health.objects.create(
                    pai=health['pai'],
                    asthme=health['asthme'],
                    allergy_food=health['allergy_food'],
                    allergy_drug=health['allergy_drug'],
                    allergy_food_details=health['allergy_food_details'],
                    allergy_drug_details=health['allergy_drug_details'],
                    record=r,
                )
                transaction.savepoint_commit(sid)
                return r

            except (KeyError) as e:
                transaction.savepoint_rollback(sid)
                print('rollback')
                if e.args:
                    return e.args[0]
                return f'Invalid payload with flag: {flag}.'

            except Exception as e:
                transaction.savepoint_rollback(sid)
                print('rollback')
                if e.args:
                    return e.args[0]
                return f'An exception occured with error: {flag}'

            return 'End of function.'

        """ Update a record """
        @staticmethod
        @transaction.atomic
        def update(child, data):
            """
            Parameters
            ----------
            arg: dict {
                child: int
                id
                school
                classroom
                date_created
                date_verified   - blank
                date_last_mod   - blank
                caf
                    q1
                    q2
                    recipent_number
                health
                    asthme
                    allergy_food 
                    allergy_drug 
                    allergy_food_details
                    allergy_drug_details
                    pai
            """

            # Instance check
            _record = Record.objects.filter(pk=data['id'])
            if not _record:
                return 'Record does not exist.'
            
            sid = transaction.savepoint()
            try:
                
                flag = 'Record object'
                r = Record(
                    id=data['id'],
                    school=data['school'],
                    classroom=data['classroom'],
                    child=child,
                )

                """ CAF Handle """
                flag = 'CAF object'
                r.caf = CAF(
                    q1=data['caf']['q1'],
                    q2=data['caf']['q2'],
                    recipent_number=data['caf']['recipent_number']
                )
                r.caf.save()

                """ Health Handle """
                flag = 'Health object'
                health = data['health']
                r.health = Health(
                    pai=health['pai'],
                    asthme=health['asthme'],
                    allergy_food=health['allergy_food'],
                    allergy_drug=health['allergy_drug'],
                    allergy_food_details=health['allergy_food_details'],
                    allergy_drug_details=health['allergy_drug_details']
                )
                r.health.save()

                r.save()
                transaction.savepoint_commit(sid)
                return r

            except (KeyError):
                transaction.savepoint_rollback(sid)
                print('rollback')
                if e.args:
                    return e.args[0]
                return f'Invalid payload with flag: {flag}.'

            except:
                transaction.savepoint_rollback(sid)
                print('rollback')
                if e.args:
                    return e.args[0]
                return f'An exception occured with error: {flag}'

            return 'End of function.'

    class Family:

        @staticmethod
        @transaction.atomic
        def create(child, parent_id, id = None):
            sid = transaction.savepoint()

            if not id:
                try:
                    id = User.objects.latest('id').id + 1
                except:
                    id = 1

            try:
                family = Family.objects.create(
                    id=id,
                    parent=parent_id,
                    child=child
                )
                transaction.savepoint_commit(sid)
                return family
            except:
                transaction.savepoint_rollback(sid)
                return 'An exception occurred during the transaction.'

        @staticmethod
        @transaction.atomic
        def update(child, data):
            pass

    class Sibling:

        @staticmethod
        def read_by_parent(parent_id):
            try:
                sibling = Sibling.objects.get(parent=parent_id)
                return sibling
            except Sibling.DoesNotExist:
                return False
        
        @staticmethod
        def read_by_child(child_id):
            try:
                sibling_child = SiblingChild.objects.get(child=child_id)
                return sibling_child.sibling
            except SiblingChild.DoesNotExist:
                return False        

        @staticmethod
        @transaction.atomic
        def create(parent_id):
            """
            Parameters
            ----------
            """
            sid = transaction.savepoint()
            try:
                sibling = Sibling.objects.create(
                    parent=parent_id
                )
                return sibling
            except:
                transaction.savepoint_rollback(sid)
                return 'An exception occurred during the transaction.'


        @staticmethod
        @transaction.atomic
        def create_bulk(data):
            """
            Parameters
            ----------
            data {
                parent - <id>
                children [
                    <child_id>
                ]
            }
            """
            sid = transaction.savepoint()
            try:
                sibling = Sibling.objects.create(
                    parent=data['parent']
                )
                for child in data['children']:
                    sibling.add_child(child)
                transaction.savepoint_commit(sid)
                return sibling
            except:
                transaction.savepoint_rollback(sid)
                return 'An exception occurred during the transaction.'

        @staticmethod
        @transaction.atomic
        def update(child, data):
            pass

    
    @staticmethod
    def read_intel(pk):
        try:
            intel = SiblingIntels.objects.get(pk=pk)
            return intel
        except SiblingIntels.DoesNotExist:
            return None

    @staticmethod
    def create_intel(sibling, data, admin=False):
        """
        Parameters
        ----------
        data {
            quotient_1          - Admin
            quotient_2          - Admin

            recipent_number     
            insurance_policy

            school_year         - Auto or admin

            date_created
            date_verified
            date_last_mod
        }
        """
        try:
            school_year = 0

            new_data = {
                'recipent_number':  data.get('recipent_number', 0),
                'insurance_policy': data.get('insurance_policy', 0)    
            }

            if admin:
                new_data['quotient_1'] = data.get('quotient_1', ChildQuotient.UNSET)
                new_data['quotient_2'] = data.get('quotient_2', ChildQuotient.UNSET)
                school_year = data.get('school_year', 0)

            if not school_year:
                _ = SchoolYear.objects.get(is_active=True)
                school_year = _.id

            intel = sibling.add_intels(new_data, school_year)    

            if intel and admin and new_data.get('verified', False):
                intel.date_verified = datetime.now()
                intel.save()

            return intel
        
        except KeyError as e:
            if e.args:
                raise InvalidPayloadException('Invalid payload ({})'.format(str(e.args[0])))
            raise InvalidPayloadException('Invalid payload')
        
        except SchoolYear.DoesNotExist:
            raise SchoolYear.DoesNotExist

        except Exception as e:
            if e.args:
                raise Exception('An error occured during intel creation process with error: ' + e.args[0])
        raise Exception('An error occured during intel creation process')


    @staticmethod
    def create_record(child_id, data):
        child = RegistrationHelper.Child.get_from_user(child_id)
        if not child:
            child = RegistrationHelper.Child.create(child_id)
            if type(child) is str:
                # print ('Child: {}'.format(child))
                return child
        record = RegistrationHelper.Record.create(child, data)
        if type(record) is str:
            # print ('Record: {}'.format(record))
            return record
        return record

    @staticmethod
    def update_record(child_id, data):
        child = RegistrationHelper.Child.get_from_user(child_id)
        if not child:
            return 'Child does not exist.'
        return RegistrationHelper.Record.update(child, data)


    @staticmethod
    def sibling_read_full(child_id):
        _sibling = RegistrationHelper.Sibling.get_from_child(child_id)
        if not _sibling:
            return 'Pas de relation trouvée pour cet enfant.'

        sibling = {}

        try:
            _parent = User.objects.get(id=_sibling.parent)
            __parent = UserSerializer(_parent)
        except User.DoesNotExist:
            return 'ID parent inconnu.'

        sibling['parent'] = __parent.data
        sibling['children'] = {}

        try:
            for x in _sibling.children.all():
                _child = User.objects.get(id=x.child)
                __child = UserSerializer(_child)

                _record = Record.objects.get(child=x.child)
                __record = RecordSerializer(_record).data

                __record['classroom'] = ChildClass(_record.classroom).name

                __record['caf']['q1'] = ChildQuotient(_record.caf.q1).name
                __record['caf']['q2'] = ChildQuotient(_record.caf.q2).name

                data = __child.data
                data['record'] = __record

                sibling['children'][_child.id] = data

        except User.DoesNotExist:
            return 'User DoesNotExist'

        except Record.DoesNotExist:
            return 'Record DoesNotExist'

        return sibling


class SchoolYearHelper:

    @staticmethod
    def read(pk=0):
        if pk == 0:
            _ = SchoolYear.objects.all()
            ss = [x.to_json() for x in _]
            return ss

        else:
            try:
                s = SchoolYear.objects.get(pk=pk)
            except SchoolYear.DoesNotExist:
                raise SchoolYear.DoesNotExist
            return s.to_json()


class ParamsHelper:
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
                stock = product.stock
                if stock.max == 0:
                    return True
                if (stock.count + mod) <= stock.max:
                    return True
                return False
            except Product.DoesNotExist:
                return False

        """ Increase count for a stock """
        @staticmethod
        def inc(product_id, mod = 1):
            try:
                product = Product.objects.get(pk=product_id)
                if product.stock.max != 0:
                    product.stock.count += mod
                    product.stock.save()
                return True
            except Product.DoesNotExist:
                return False

        """ Decrease count for a stock """
        @staticmethod
        def dec(product_id, mod = 1):
            try:
                product = Product.objects.get(pk=product_id)
                if product.stock.max == 0:
                    return True

                if (product.stock.count - mod) >= 0:
                    product.stock.count -= mod
                    product.stock.save()
                return True
            except Product.DoesNotExist:
                return False


class OrderHelper:

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
        Return an age for a given date and start point (mod) 
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
            verify_result = {
                'status': 'Failure',
            }

            # Gather data to prevent index errors
            try:
                payer_id = data['payer']
                caster_id = data['caster']

                # peri = data['peri']
                # alsh = data['alsh']
                cart = data['cart']

            except KeyError as e:
                verify_result['message'] = 'Payload invalide avec erreur ({})'.format(str(e))
                return verify_result

            # Gather payer intels
            parent = OrderHelper.Verifications._verify_payer(payer_id)
            if type(parent) is str:
                verify_result['message'] = parent
                return verify_result

            # Gather caster intels if different
            if payer_id != caster_id:
                caster = OrderHelper.Verifications._verify_caster(caster_id)
                if type(caster) is str:
                    verify_result['message'] = caster
                    return verify_result
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

                # Check peri
                # print('3')
                # amount, tickets, tickets_invalid = OrderHelper.Verifications._verify_peri(
                #     sibling, products_peri, peri)

                # # Check alsh
                # # print('2')
                # _amount, _tickets, _tickets_invalid = OrderHelper.Verifications._verify_alsh(
                #     sibling, products_alsh, alsh)

            except Exception as e:
                verify_result['message'] = str(e)
                return verify_result

            # print('1')

            # verify_result['amount'] = amount + _amount
            # verify_result['tickets'] = tickets + _tickets
            # verify_result['tickets_invalid'] = tickets_invalid + \
            #     _tickets_invalid

            # print ('amount: ' + str(amount))

            verify_result['amount'] = amount
            verify_result['tickets'] = tickets
            verify_result['tickets_invalid'] = tickets_invalid

            if verify_result['tickets']:
                verify_result['status'] = 'Success'
            else:
                verify_result['message'] = 'Le panier contient des erreurs.'

            return verify_result


        @staticmethod
        def _verify_payer(payer_id):
            try:
                parent = User.objects.get(id=payer_id)

            except User.DoesNotExist:
                return 'Payeur introuvable avec l\'ID ({}).'.format(payer_id)

            # Role
            is_parent = False
            for role in parent.roles.all():
                if role.slug == 'parent':
                    is_parent = True
                    break
            
            if not is_parent:
                return 'Le payeur n\' est pas un parent.' 

            return parent


        @staticmethod
        def _verify_caster(caster_id):
            try:
                caster = User.objects.get(id=caster_id)
            except User.DoesNotExist:
                return 'Casteur introuvable avec l\'ID ({}).'.format(payer_id)

            # Role
            is_admin = False
            for role in caster.roles.all():
                if role.slug == 'admin' or role.slug == 'ap_admin':
                    is_admin = True
                    break
            
            if not is_admin:
                return 'Le casteur n\' est pas un administrateur.' 
            return caster


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
        @staticmethod
        def _verify_peri(sibling, products, peri):
            amount = 0

            tickets = []
            tickets_invalid = []

            for month in peri:

                # Check key errors
                try:
                    product_id = month['product']
                    children_ids = month['children']
                except KeyError as e:
                    raise Exception('KeyError with error ' + str(e))

                # Check there are children
                if not children_ids:
                    continue

                # Product lookup
                try:
                    product = products.get(id=product_id)
                except Product.DoesNotExist:
                    product = None

                # Look up for child
                _ = []
                for child_id in children_ids:

                    # Check product
                    if not product:
                        tickets_invalid.append({
                            'payee': child_id,
                            'product': product_id,
                            'obs': 'Product not found.'
                        })
                        continue

                    # Check children in sibling
                    if not child_id in sibling:
                        tickets_invalid.append({
                            'payee': child_id,
                            'product': product_id,
                            'obs': 'Child is not bind to parent.'
                        })
                        continue

                    # Check child never bought product
                    if OrderHelper.Verifications._has_bought(child_id, product_id):
                        tickets_invalid.append({
                            'payee': child_id,
                            'product': product_id,
                            'obs': 'Product already bought.'
                        })
                        continue

                    # if there is no problems
                    _.append(child_id)

                # If no child - continue
                if not _:
                    continue

                count = len(_)

                # print ('product_id: ', product_id)
                # print ('count: ', count)

                # Set price
                index = min(count, len(TARIFS_PERI))
                amount += TARIFS_PERI[index - 1]

                # print ('index: ', index)
                # print ('amount: ', amount)

                for child_id in _:
                    price = TARIFS_PERI[index - 1] / count
                    # price = round(TARIFS_PERI[index - 1] / count)
                    tickets.append({
                        'payee': child_id,
                        'price': price,
                        'product': product_id
                    })

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
        @staticmethod
        def _verify_alsh(sibling, products, alsh):
            # NOTE
            # Products should be ordered by trimesters

            amount = 0

            tickets = []
            tickets_invalid = []

            # print (f'sibling: {sibling}')

            for x in alsh:

                # Cache for product categories
                categories = {}

                # Check keys errors
                try:
                    child_id = x['child']
                    products_ids = x['products']

                    # print (f'child_id: {child_id}')
                    # print (f'products_ids: {products_ids}')

                except KeyError as e:
                    raise Exception('KeyError with error ' + str(e))

                # Check there are products
                if not products_ids:
                    continue

                # Check child is in sibling
                if child_id not in sibling:
                    # Return an unique ticket cuz we don't know if products are corrects -_-
                    tickets_invalid.append({
                        'payee': child_id,
                        'product': -1,
                        'obs': 'Child is not bind to parent.'
                    })
                    continue

                # Get child intels and records
                try:
                    child = User.objects.get(id=child_id)
                    record = Record.objects.get(child=child_id)
                except User.DoesNotExist:
                    tickets_invalid.append({
                        'payee': child_id,
                        'product': -1,
                        'obs': 'Child does not exist.'
                    })
                    continue
                except Record.DoesNotExist:
                    tickets_invalid.append({
                        'payee': child_id,
                        'product': -1,
                        'obs': 'Child record does not exist.'
                    })
                    continue

                age_range = 2
                if not record.classroom:
                    tickets_invalid.append({
                        'payee': child_id,
                        'product': -1,
                        'obs': 'Classroom not set.'
                    })
                if record.classroom >= 1 and record.classroom <= 4:
                    age_range = 1

                # Process products
                # Do a first check of products
                # And order them by category
                for product_id in products_ids:

                    # Get product
                    try:
                        product = products.get(id=product_id)
                    except Product.DoesNotExist:
                        # print ('x')
                        tickets_invalid.append({
                            'payee': child_id,
                            'product': product_id,
                            'obs': 'Product not found.'
                        })
                        continue

                    # Check stock
                    if not ParamsHelper.Stock.has_stock(product_id):
                        tickets_invalid.append({
                            'payee': child_id,
                            'product': product_id,
                            'obs': 'Product out of stock.'
                        })

                    # Check subcategory (MINUS/PLUS 6)
                    if age_range != product.subcategory:
                        tickets_invalid.append({
                            'payee': child_id,
                            'product': product_id,
                            'obs': 'Wrong product for the age.'
                        })
                        continue

                    # Check order
                    # here cuz we don't want a bought product to be in categories list
                    if OrderHelper.Verifications._has_bought(child_id, product_id):
                        tickets_invalid.append({
                            'payee': child_id,
                            'product': product_id,
                            'obs': 'Product already bought.'
                        })
                        continue

                    # if child has less than 3yo he is not eligible
                    # Check age at the product date
                    # stop processing and continue
                    if OrderHelper.Verifications._get_age_from_date(child.dob, product.date) < 3:
                        # print('x')
                        # Check order
                        # if OrderHelper.Verifications._has_bought(child_id, product_id):
                        #     tickets_invalid.append({
                        #         'payee': child_id,
                        #         'product': product_id,
                        #         'obs': 'Product already bought.'
                        #     })
                        #     continue

                        amount += product.price
                        tickets.append({
                            'payee': child_id,
                            'price': product.price,
                            'product': product_id
                        })
                        continue

                    # if every verifications succeed
                    # add product for further verifications
                    # Order products by category
                    if product.category not in categories:
                        categories[product.category] = {
                            'cart': [product_id],
                            'owned': []
                        }
                    else:
                        categories[product.category]['cart'].append(product_id)

                for key in categories:
                    category = categories[key]

                    # 1st instance check
                    if not category['owned']:
                        # Get products by category
                        _products = products.filter(category=key)
                        for _product in _products:
                            _tickets = Ticket.objects.filter(
                                payee=child_id, product=_product.id)
                            if _tickets:
                                category['owned'].append(_product.id)

                    count = len(category['cart']) + len(category['owned'])
                    # print (f'count: {count}')

                    for product_id in category['cart']:

                        # Check ticket
                        if product_id in category['owned']:
                            tickets_invalid.append({
                                'payee': child_id,
                                'product': product_id,
                                'obs': 'Product already bought.'
                            })
                            continue

                        # Get product
                        # Double check - it's not supposed to happen
                        try:
                            product = products.get(id=product_id)
                        except Product.DoesNotExist:
                            tickets_invalid.append({
                                'payee': child_id,
                                'product': product_id,
                                'obs': 'Product not found.'
                            })
                            continue
                        
                        count = 5
                        if count > 4:
                            # print ('count > 4')
                            # Check product trimester
                            q = 'q2'
                            # Product category enums - refer to models
                            if product.category in [10, 11, 12, 13, 14, 15]:
                                q = 'q1'

                            # Maths
                            price = product.price  # NE
                            price = product.price_q2 if getattr(record.caf, q) == 2 else price  # Q2
                            price = product.price_q1 if getattr(record.caf, q) == 3 else price  # Q1

                            amount += price
                            # print (price)
                            tickets.append({
                                'payee': child_id,
                                'price': price,
                                'product': product_id
                            })

                        else:
                            # print ('count < 4')
                            amount += product.price
                            tickets.append({
                                'payee': child_id,
                                'price': product.price,
                                'product': product_id
                            })

            return amount, tickets, tickets_invalid


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

                        # July exception
                        if key == 1011:
                            price = 5.0
                            
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
        verify_result = OrderHelper.verify(verify_payload, True)

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

    """ 
        They should be 2 kind of verifications
        Soft: Don't check client intels
        Hard: Check client intels and deduce the amount by his credit
    """
    @staticmethod
    def verify(data, soft=False):
        verify_result = OrderHelper.Verifications._verify(data)

        if soft:
            return verify_result

        # If hard
        try:
            client = AClient.objects.get(pk=data['payer'])
            credit = client.credit
        
            if credit > verify_result['amount']:
                verify_result['amount'] = 0

            else:
                verify_result['amount'] = verify_result['amount'] - credit
                            
        # If client does not exist return normal amount
        except Exception as e:
            # print (e)
            pass

        return verify_result

    """
    Convert a str date into a date according to format %Y-%m-%d %H:%M:%S
    And localize it (non-naive)
    """
    @staticmethod
    def _localize(date):
        if type(date) is str:
            # _ = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            _ = datetime.fromisoformat(date)
        else:
            _ = date
        return pytz.utc.localize(_)

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
                date = OrderHelper._localize(datetime.now())
            else:
                date = OrderHelper._localize(data['date'])

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

            status_date = OrderHelper._localize(status['date']) if 'date' in status else date
            
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


class _RegistrationHelper:
    
    class Child:

        @staticmethod
        def get(pk):
            try:
                return Child.objects.get(pk=pk)
            except:
                return None

        @staticmethod
        def get_from_user(user):
            try:
                return Child.objects.get(user=user)
            except:
                return None
        
        """ Create a child """
        @staticmethod
        @transaction.atomic
        def create(id):
            sid = transaction.savepoint()
            try:
                child = Child.objects.create(
                    id=id,
                    user=id
                )
                transaction.savepoint_commit(sid)
                return child
            except:
                transaction.savepoint_rollback(sid)
                return 'An error occurred during the transaction.'

        """ Update a child """
        @staticmethod
        @transaction.atomic
        def update(data):
            sid = transaction.savepoint()
            try:
                child = Child.objects.get(user=data['id'])
                child.user = data['user']
                transaction.savepoint_commit(sid)
                return child
            except Child.DoesNotExist:
                transaction.savepoint_rollback(sid)
                return 'Child does not exist.'
            except:
                transaction.savepoint_rollback(sid)
                return 'An error occurred during the transaction.'

        @staticmethod
        def delete(pk):
            Child.objects.filter(pk=pk).delete()

        @staticmethod
        def delete_from_user(user):
            Child.objects.filter(user=user).delete()

    class Record:
    
        """ Create a record """
        @staticmethod
        @transaction.atomic
        def create(child, data):
            """
            Parameters
            ----------
            arg: dict {
                id
                school
                classroom
                date_created
                date_verified   - blank
                date_last_mod   - blank
                caf
                    q1
                    q2
                    recipent_number
                health
                    asthme
                    allergy_food 
                    allergy_drug 
                    allergy_food_details
                    allergy_drug_details
                    pai
            """
            sid = transaction.savepoint()

            try:
                id = data['id']
            except KeyError:
                id = User.objects.latest('id').id + 1
            except:
                id = 1

            try:
                flag = 'Record object'
                r = Record.objects.create(
                    id=id,
                    school=data['school'],
                    classroom=data['classroom'],
                    child=child,
                )

                """ CAF Handle """
                flag = 'CAF object'

                c = CAF.objects.create(
                    q1=data['caf']['q1'],
                    q2=data['caf']['q2'],
                    recipent_number=data['caf']['recipent_number'],
                    record=r
                )

                """ Health Handle """
                flag = 'Health object'
                health = data['health']
                h = Health.objects.create(
                    pai=health['pai'],
                    asthme=health['asthme'],
                    allergy_food=health['allergy_food'],
                    allergy_drug=health['allergy_drug'],
                    allergy_food_details=health['allergy_food_details'],
                    allergy_drug_details=health['allergy_drug_details'],
                    record=r,
                )
                transaction.savepoint_commit(sid)
                return r

            except (KeyError) as e:
                transaction.savepoint_rollback(sid)
                print('rollback')
                if e.args:
                    return e.args[0]
                return f'Invalid payload with flag: {flag}.'

            except Exception as e:
                transaction.savepoint_rollback(sid)
                print('rollback')
                if e.args:
                    return e.args[0]
                return f'An exception occured with error: {flag}'

            return 'End of function.'

        """ Update a record """
        @staticmethod
        @transaction.atomic
        def update(child, data):
            """
            Parameters
            ----------
            arg: dict {
                child: int
                id
                school
                classroom
                date_created
                date_verified   - blank
                date_last_mod   - blank
                caf
                    q1
                    q2
                    recipent_number
                health
                    asthme
                    allergy_food 
                    allergy_drug 
                    allergy_food_details
                    allergy_drug_details
                    pai
            """

            # Instance check
            _record = Record.objects.filter(pk=data['id'])
            if not _record:
                return 'Record does not exist.'
            
            sid = transaction.savepoint()
            try:
                
                flag = 'Record object'
                r = Record(
                    id=data['id'],
                    school=data['school'],
                    classroom=data['classroom'],
                    child=child,
                )

                """ CAF Handle """
                flag = 'CAF object'
                r.caf = CAF(
                    q1=data['caf']['q1'],
                    q2=data['caf']['q2'],
                    recipent_number=data['caf']['recipent_number']
                )
                r.caf.save()

                """ Health Handle """
                flag = 'Health object'
                health = data['health']
                r.health = Health(
                    pai=health['pai'],
                    asthme=health['asthme'],
                    allergy_food=health['allergy_food'],
                    allergy_drug=health['allergy_drug'],
                    allergy_food_details=health['allergy_food_details'],
                    allergy_drug_details=health['allergy_drug_details']
                )
                r.health.save()

                r.save()
                transaction.savepoint_commit(sid)
                return r

            except (KeyError):
                transaction.savepoint_rollback(sid)
                print('rollback')
                if e.args:
                    return e.args[0]
                return f'Invalid payload with flag: {flag}.'

            except:
                transaction.savepoint_rollback(sid)
                print('rollback')
                if e.args:
                    return e.args[0]
                return f'An exception occured with error: {flag}'

            return 'End of function.'

    class Family:

        @staticmethod
        @transaction.atomic
        def create(child, parent_id, id = None):
            sid = transaction.savepoint()

            if not id:
                try:
                    id = User.objects.latest('id').id + 1
                except:
                    id = 1

            try:
                family = Family.objects.create(
                    id=id,
                    parent=parent_id,
                    child=child
                )
                transaction.savepoint_commit(sid)
                return family
            except:
                transaction.savepoint_rollback(sid)
                return 'An exception occurred during the transaction.'

        @staticmethod
        @transaction.atomic
        def update(child, data):
            pass

    class Sibling:

        @staticmethod
        def read_by_parent(parent_id):
            try:
                sibling = Sibling.objects.get(parent=parent_id)
                return sibling
            except Sibling.DoesNotExist:
                return None
        
        @staticmethod
        def get_from_child(child_id):
            try:
                sibling_child = SiblingChild.objects.get(child=child_id)
                return sibling_child.sibling
            except SiblingChild.DoesNotExist:
                return None        

        @staticmethod
        def child(id):
            child = RegistrationHelper.Child.get(id)
            if not child:
                child = RegistrationHelper.Child.create(id)
                if type(child) is str:
                    return child

        @staticmethod
        @transaction.atomic
        def create(data):
            sid = transaction.savepoint()
            try:
                sibling = Sibling.objects.create(
                    parent=data['parent']
                )
                for _child in data['children']:
                    child = RegistrationHelper.Child.get(_child)
                    if not child:
                        continue
                    sibling.children.add(SiblingChild.objects.create(
                        child=child,
                        sibling=sibling
                    ))
                transaction.savepoint_commit(sid)
                return sibling
            except:
                transaction.savepoint_rollback(sid)
                return 'An exception occurred during the transaction.'

        @staticmethod
        @transaction.atomic
        def update(child, data):
            pass

    @staticmethod
    def create_record(child_id, data):
        child = RegistrationHelper.Child.get_from_user(child_id)
        if not child:
            child = RegistrationHelper.Child.create(child_id)
            if type(child) is str:
                print ('Child: {}'.format(child))
                return child
        record = RegistrationHelper.Record.create(child, data)
        if type(record) is str:
            print ('Record: {}'.format(record))
            return record
        return record

    @staticmethod
    def update_record(child_id, data):
        child = RegistrationHelper.Child.get_from_user(child_id)
        if not child:
            return 'Child does not exist.'
        return RegistrationHelper.Record.update(child, data)


    @staticmethod
    def sibling_read_full(child_id):
        _sibling = RegistrationHelper.Sibling.get_from_child(child_id)
        if not _sibling:
            return 'Pas de relation trouvée pour cet enfant.'

        sibling = {}

        try:
            _parent = User.objects.get(id=_sibling.parent)
            __parent = UserSerializer(_parent)
        except User.DoesNotExist:
            return 'ID parent inconnu.'

        sibling['parent'] = __parent.data
        sibling['children'] = {}

        try:
            for x in _sibling.children.all():
                _child = User.objects.get(id=x.child)
                __child = UserSerializer(_child)

                _record = Record.objects.get(child=x.child)
                __record = RecordSerializer(_record).data

                __record['classroom'] = ChildClass(_record.classroom).name

                __record['caf']['q1'] = ChildQuotient(_record.caf.q1).name
                __record['caf']['q2'] = ChildQuotient(_record.caf.q2).name

                data = __child.data
                data['record'] = __record

                sibling['children'][_child.id] = data

        except User.DoesNotExist:
            return 'User DoesNotExist'

        except Record.DoesNotExist:
            return 'Record DoesNotExist'

        return sibling


@transaction.atomic
def create(child, data):
    """
    Parameters
    ----------
    arg: dict {
        id
        school
        classroom
        date_created
        date_verified   - blank
        date_last_mod   - blank
        caf
            q1
            q2
            recipent_number
        health
            asthme
            allergy_food 
            allergy_drug 
            allergy_food_details
            allergy_drug_details
            pai
    """
    sid = transaction.savepoint()

    try:
        id = data['id']
    except KeyError:
        id = User.objects.latest('id').id + 1
    except:
        id = 1

    try:
        flag = 'Record object'
        r = Record.objects.create(
            id=id,
            school=data['school'],
            classroom=data['classroom'],
            child=data['child'],
        )

        """ Health Handle """
        flag = 'Health object'
        health = data['health']
        h = Health.objects.create(
            pai=health['pai'],
            asthme=health['asthme'],
            allergy_food=health['allergy_food'],
            allergy_drug=health['allergy_drug'],
            allergy_food_details=health['allergy_food_details'],
            allergy_drug_details=health['allergy_drug_details'],
            record=r,
        )
        transaction.savepoint_commit(sid)
        return r

    except (KeyError) as e:
        transaction.savepoint_rollback(sid)
        print('rollback')
        if e.args:
            return e.args[0]
        return f'Invalid payload with flag: {flag}.'

    except Exception as e:
        transaction.savepoint_rollback(sid)
        print('rollback')
        if e.args:
            return e.args[0]
        return f'An exception occured with error: {flag}'

    return 'End of function.'