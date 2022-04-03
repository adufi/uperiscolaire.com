import pytz
import json

from datetime import datetime

from django.db import transaction
from django.http import QueryDict
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from users.models import UserAuth, Role, User, UserPhone, UserEmail, UserAddress, UserPhoneType, UserEmailType, UserAddressType
from users.serializers import UserSerializer, UserSerializerShort, EmailSerializer, PhoneSerializer, AddressSerializer, RoleSerializerShort
from users.utils_registers import create_user, create_user_migration

from order.models import Client, ClientCredit, OrderStock, Order, OrderMethod, OrderStatus, Ticket, TicketStatus, StatusEnum, OrderTypeEnum, MethodEnum
from order.serializers import OrderSerializer

from users.models import User
from params.models import  Product, ProductStock

from registration.models import Sibling, SiblingChild, Family, Record, CAF, Health, ChildPAI, ChildClass, ChildQuotient
from registration.serializers import RecordSerializer


NAME = 'Paiement ALSH/PERI 2019-2020'
TARIFS_PERI = [20, 32, 40, 60]
PAGINATOR_MAX_PAGE = 25


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

    if processData:
        _data = processData(list(paginator_page))
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

                auth = UserAuth.objects.filter(email=email).first()

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
                online_id   
                dob                 - Optional - Year-month-day hours:minutes:seconds
                is_active           - Optional - default True
                is_auto_password    - Optional - default False
                date_created?       - auto
                date_confirmed?     - auto
                
                auth                - Optional
                    id              - Optional
                    email
                    password1
                    password2

                roles []            
                    role (slug)     - str
                
                phones              - Optional
                    type
                    phone
                
                emails []           - Optional
                    is_main
                    email
                    type
                
                addresses           - Optional
                    name
                    addresstype
                    is_main
                    address1
                    address2
                    zip_code
                    city
                    country
            }

            Returns
            -------
            """
            error = ''
            sid = transaction.savepoint()

            if 'id' in data:
                id = data['id']

                if not update:
                    _user = User.objects.filter(pk=id) 
                    if _user:
                        return f'Collision detected for ID ({id}).'
            else:
                try:
                    id = User.objects.latest('id').id + 1
                except:
                    id = 1

            try:
                error = 'Failed to create user'

                user = User(
                    id=id,
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    dob=data.get('dob', None),
                    is_active=data.get('is_active', True),
                    online_id=data.get('online_id', 0),
                    is_auto_password=data.get('is_auto_password', False)
                )

                # Auth
                error = 'Failed to create auth'
                if 'auth' in data and data['auth']:
                    # if id in payload 
                    # update auth
                    if 'id' in data['auth']:
                        auth = UsersHelper._update_auth(data['auth'])
                    
                    # create auth
                    else:
                        auth = UsersHelper._create_auth(data['auth'])

                    if type(auth) is str:
                        return auth

                    user.auth = auth
                    user.auth.save()

                user.save()

                """ Add secondary intels (addresses, phones) """
                # Roles
                error = 'Failed to create roles'
                if 'roles' in data:
                    # Clear previous roles
                    user.roles.clear()

                    # Add roles
                    r = UsersHelper._create_role(user, data['roles'])
                    if type(r) is str:
                        print(f'r = {r}')
                        raise Exception(r)

                # Phones
                error = 'Failed to create phone'
                if 'phones' in data:
                    # Clear previous phones
                    user.phones.all().delete()


                    r = UsersHelper._create_phone(user, data['phones'])
                    if type(r) is str:
                        raise Exception(r)

                # Emails
                error = 'Failed to create emails'
                if 'emails' in data:
                    # Clear previous emails
                    user.emails.all().delete()

                    r = UsersHelper._create_email(user, data['emails'])
                    if type(r) is str:
                        raise Exception(r)
                
                # Addresses
                error = 'Failed to create addresses'
                if 'addresses' in data:
                    # Clear previous addresses
                    user.addresses.all().delete()

                    r = UsersHelper._create_address(user, data['addresses'])
                    if type(r) is str:
                        raise Exception(r)

                transaction.savepoint_commit(sid)
                return user

            except Exception as e:
                transaction.savepoint_rollback(sid)
                print('rollback')
                print (error)
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


    """ Get user status """
    @staticmethod
    def status():
        pass
    
    
    """ List users - ADMIN """
    @staticmethod
    def users_read(request, role=''):
        """ 
        Return a set of users for a given role 
        Return whole users if role is empty
        """
        _users = None
        if role:
            _users = User.objects.filter(roles__slug=role)
        else:
            _users = User.objects.all()
        
        if _users:
            page = int(request.GET.get('page', 1))

            def processData(data):
                return UserSerializer(data, many=True).data

            return paginate(_users, page, processData)
            # return UsersHelper._users_read(request, _users)
        return False


    """ Read user profile """
    @staticmethod
    def user_read(pk):
        _user = UsersHelper._user_read(pk)
        if not _user:
            return False

        return _user

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

        except KeyError:
            return 'Values can\'t be empty'

        return UsersHelper.User.update(new_data)


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
            Register family
        """
        try:
            new_data = {
                'parent_id':    data['parent_id'],

                'dob':          data['dob'],
                'first_name':   data['first_name'],
                'last_name':    data['last_name'],
            }

            # if admin
            # new_data['online_id'] = data.get('online_id', 0)
            # new_data['is_active'] = data.get('is_active', True)
            # new_data['is_auto_password'] = data.get('is_auto_password', False)

        except KeyError:
            return 'Values can\'t be empty'

        except Exception as e:
            if e.args:
                return 'Invalid payload with error: ' + e.args[0]
            return 'Invalid payload'

        sid = transaction.savepoint()

        try:
            id = User.objects.latest('id').id + 1
            
            user = User.objects.create(
                id=id,
                dob=new_data['dob'],
                last_name=new_data['last_name'],
                first_name=new_data['first_name'],
                is_active=True
            )

            child_role = Role.objects.get(slug='child')
            user.roles.add(child_role)

            # Sibling & Family
            sibling = RegistrationHelper.Sibling.read_by_parent(new_data['parent_id'])
            if not sibling:
                

            sibling.add_child(user.id)

            Family.objects.create(
                child=user.id,
                parent=new_data['parent_id']
            )

            transaction.savepoint_commit(sid)
            return user

        except Role.DoesNotExist:
            transaction.savepoint_rollback(sid)
            return 'Role does not exist'
            
        except Exception as e:
            transaction.savepoint_rollback(sid)
            if e.args:
                return 'Invalid payload with error: ' + e.args[0]
            return 'Invalid payload'

        return 'An error occured during the process'


    """ Return a serialized user for a given pk """
    
    """ Return a raw user for a given pk """
    @staticmethod
    def _user_read(pk):
        try:
            _user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return False
        return _user


    """
    Return ...
    """

    """ Shortcut to create an user """ 
    @staticmethod
    def post(data):
        """
        Parameters
        ----------
        arg1: dict {
            id                  - Optional
            last_name          
            first_name
            online_id           - Optional - default 0
            dob                 - Optional - Year-month-day hours:minutes:seconds
            is_active           - Optional - default True
            is_auto_password    - Optional - default False
            date_created?       - auto
            date_confirmed?     - auto
            
            auth                - Optional
                id              - Optional
                email
                password1
                password2

            roles []            
                role (slug)     - str
            
            phones              - Optional
                type
                phone
            
            emails []           - Optional
                is_main
                email
                type
            
            addresses           - Optional
                name
                type
                is_main
                address1
                address2
                zip_code
                city
                country
        }
        arg2: boolean

        Returns
        -------
        """
        data['is_active'] = True
        data['is_auto_password'] = False
        data['roles'] = ['parent']
        return UsersHelper._users(data)

    """ """
    @staticmethod
    def update(data):
        """
        Parameters
        ----------
        arg1: dict {
            id                  - Optional
            last_name          
            first_name
            online_id           - Optional - default 0
            dob                 - Optional - Year-month-day hours:minutes:seconds
            is_active           - Optional - default True
            is_auto_password    - Optional - default False
            date_created?       - auto
            date_confirmed?     - auto
            
            auth                - Optional
                id              - Optional
                email
                password1
                password2

            roles []            
                role (slug)     - str
            
            phones              - Optional
                type
                phone
            
            emails []           - Optional
                is_main
                email
                type
            
            addresses           - Optional
                name
                type
                is_main
                address1
                address2
                zip_code
                city
                country
        }
        arg2: boolean

        Returns
        -------
        """
        data['is_active'] = True
        data['is_auto_password'] = False
        data['roles'] = ['parent']
        return UsersHelper._users(data, True)

    """ Create/Update an user """
    @staticmethod
    @transaction.atomic
    def _users(data, update=False):
        """
        Parameters
        ----------
        arg1: dict {
            id                  - Optional
            last_name          
            first_name
            online_id   
            dob                 - Optional - Year-month-day hours:minutes:seconds
            is_active           - Optional - default True
            is_auto_password    - Optional - default False
            date_created?       - auto
            date_confirmed?     - auto
            
            auth                - Optional
                id              - Optional
                email
                password1
                password2

            roles []            
                role (slug)     - str
            
            phones              - Optional
                type
                phone
            
            emails []           - Optional
                is_main
                email
                type
            
            addresses           - Optional
                name
                addresstype
                is_main
                address1
                address2
                zip_code
                city
                country
        }
        arg2: boolean

        Returns
        -------
        """
        error = ''
        sid = transaction.savepoint()

        if 'id' in data:
            id = data['id']

            if not update:
                _user = User.objects.filter(pk=id) 
                if _user:
                    return f'Collision detected for ID ({id}).'
        else:
            try:
                id = User.objects.latest('id').id + 1
            except:
                id = 1

        try:
            error = 'Failed to create user'

            user = User(
                id=id,
                first_name=data['first_name'],
                last_name=data['last_name'],
                dob=data.get('dob', None),
                is_active=data.get('is_active', True),
                online_id=data.get('online_id', 0),
                is_auto_password=data.get('is_auto_password', False)
            )

            # Auth
            error = 'Failed to create auth'
            if 'auth' in data and data['auth']:
                # if id in payload 
                # update auth
                if 'id' in data['auth']:
                    auth = UsersHelper._update_auth(data['auth'])
                
                # create auth
                else:
                    auth = UsersHelper._create_auth(data['auth'])

                if type(auth) is str:
                    return auth

                user.auth = auth
                user.auth.save()

            user.save()

            """ Add secondary intels (addresses, phones) """
            # Roles
            error = 'Failed to create roles'
            if 'roles' in data:
                # Clear previous roles
                user.roles.clear()

                # Add roles
                r = UsersHelper._create_role(user, data['roles'])
                if type(r) is str:
                    print(f'r = {r}')
                    raise Exception(r)

            # Phones
            error = 'Failed to create phone'
            if 'phones' in data:
                # Clear previous phones
                user.phones.all().delete()


                r = UsersHelper._create_phone(user, data['phones'])
                if type(r) is str:
                    raise Exception(r)

            # Emails
            error = 'Failed to create emails'
            if 'emails' in data:
                # Clear previous emails
                user.emails.all().delete()

                r = UsersHelper._create_email(user, data['emails'])
                if type(r) is str:
                    raise Exception(r)
            
            # Addresses
            error = 'Failed to create addresses'
            if 'addresses' in data:
                # Clear previous addresses
                user.addresses.all().delete()

                r = UsersHelper._create_address(user, data['addresses'])
                if type(r) is str:
                    raise Exception(r)

            transaction.savepoint_commit(sid)
            return user

        except Exception as e:
            transaction.savepoint_rollback(sid)
            print('rollback')
            print (error)
            if e.args:
                return e.args[0]
            return f'An exception occured with error: {error}'

        return 'End of function.'

        # except:
        #     transaction.savepoint_rollback(sid)
        #     print ('rollback')
        #     return f'An exception occured with error: {error}'

    """ Create an auth from a payload """
    @staticmethod
    def _create_auth(data):
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
        on success: Model
        """
        try:
            email = data['email']
            password1 = data['password1']
            password2 = data['password2']

            if password1 != password2:
                return 'Passwords didn\'t matched.'

            auth = UserAuth.objects.filter(email=email).first()

            if not auth:
                auth = UserAuth(
                    email=email,
                    password=password1
                )
                # auth.save()
                return auth
            else:
                return 'Email already exist.'
        except:
            return 'Invalid payload.'

    """ Update auth """
    @staticmethod
    def _update_auth(data):
        """
        Parameter
        ---------
        arg => dict {
            id
            email
            password1
            password2
        }

        Returns
        -------
        on error: str
        on success: Model
        """
        try:
            id = data['id']
            auth = UserAuth.objects.get(id=id)

            email = data['email']
            # if email is different test it
            if email != auth.email:
                _auth = UserAuth.objects.filter(email=email).first()
                if _auth:
                    return 'Email already exist.'

            password1 = data['password1']
            password2 = data['password2']

            if password1 != password2:
                return 'Passwords didn\'t matched.'

            auth = UserAuth(
                email=email,
                password=password1
            )
            # auth.save()
            return auth

        except User.DoesNotExist:
            return 'User not found.'

        except:
            return 'Invalid payload.'

    @staticmethod
    def _create_role(user, roles):
        try:
            for role in roles:
                r = Role.objects.get(slug=role)
                user.roles.add(r)
        except Role.DoesNotExist:
                return 'Role doesn\'t exist.'
        except:
            print('except')
            return 'An exception occured during role process.'
        return True

    # is_main to handle
    @staticmethod
    def _create_phone(user, phones):
        try:
            for phone in phones:
                type = phone['type'] if 'type' in phone else UserPhoneType.HOME.value

                user.phones.add(UserPhone.objects.create(
                    user=user,
                    phone=phone['phone'],
                    phone_type=type
                ))
        except Exception as e:
            return f'An exception occured during phone process with error {e.args[0]}.'
        return True

    @staticmethod
    def _create_email(user, emails):
        has_main = False
        try:
            for email in emails:
                e = UserEmail(
                    user=user,
                    email=email['email'],
                )

                e.email_type = email['type'] if 'type' in email else UserEmailType.HOME.value

                if ('is_main' in email) and (email['is_main']) and not has_main:
                    e.is_main = True
                    has_main = True

                e.save()
                user.emails.add(e)

            # Ensure one is_main is set to True
            if not has_main and len(emails) > 0:
                user.emails[0].is_main = True

        except (KeyError):
            return 'KeyError occured during email process.'
        except:
            return 'An exception occured during email process.'
        return True

    @staticmethod
    def _create_address(user, addresses):
        has_main = False
        try:
            for address in addresses:
                a = UserAddress(
                    user=user,
                    name=address['name'],
                    # address_type=address['type'],
                    address1=address['address1'],
                    address2=address['address2'],
                    zip_code=address['zip_code'],
                    city=address['city'],
                    country=address['country'],
                )

                a.type = address['type'] if 'type' in address else UserAddressType.HOME.value

                if 'is_main' in address and address['is_main'] and not has_main:
                    a.is_main = True
                    has_main = True

                a.save()
                user.addresses.add(a)

            # Ensure one is_main is set to True
            if not has_main and len(addresses) > 0:
                user.addresses[0].is_main = True

        except (KeyError):
            return 'KeyError occured during address process.'
        except:
            return 'An exception occured during address process.'
        return True


    """ Old paginate users """
    @staticmethod
    def _users_read(request, _users):
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
                for status in t.status.all():
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

            products_peri = Product.objects.filter(category=1)
            products_alsh = Product.objects.exclude(category=1)

            # Gather data to prevent index errors
            try:
                payer_id = data['payer']
                caster_id = data['caster']

                peri = data['peri']
                alsh = data['alsh']

            except KeyError as e:
                verify_result['message'] = 'KeyError with error ' + str(e)
                return verify_result

            # Gather payer intels
            # try:
            #     parent = User.objects.get(id=payer_id)

            # except User.DoesNotExist:
            #     verify_result['message'] = 'Payer does not exist with ID: ' + str(payer_id)
            #     return verify_result

            # Gather caster intels if different
            # caster = None
            # if caster_id != payer_id:
            #     try:
            #         caster = User.objects.get(id=caster_id)

            #     except User.DoesNotExist:
            #         verify_result['message'] = 'Caster does not exist with ID: ' + str(caster_id)
            #         return verify_result

            # Get sibling
            try:
                _sibling = Sibling.objects.get(parent=payer_id)
                sibling = []

                for s in _sibling.children.all():
                    sibling.append(s.child.id)

            except Sibling.DoesNotExist:
                verify_result['message'] = 'Sibling does not exist for payer.'
                return verify_result

            # Start PERI and ALSH check
            amount = 0

            tickets = []
            tickets_invalid = []

            try:
                # Check peri
                # print('3')
                amount, tickets, tickets_invalid = OrderHelper.Verifications._verify_peri(
                    sibling, products_peri, peri)

                # Check alsh
                # print('2')
                _amount, _tickets, _tickets_invalid = OrderHelper.Verifications._verify_alsh(
                    sibling, products_alsh, alsh)

            except Exception as e:
                verify_result['message'] = str(e)
                return verify_result

            # print('1')

            verify_result['amount'] = amount + _amount
            verify_result['tickets'] = tickets + _tickets
            verify_result['tickets_invalid'] = tickets_invalid + \
                _tickets_invalid

            if verify_result['tickets']:
                verify_result['status'] = 'Success'

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

                print ('product_id: ', product_id)
                print ('count: ', count)

                # Set price
                index = min(count, len(TARIFS_PERI))
                amount += TARIFS_PERI[index - 1]

                print ('index: ', index)
                print ('amount: ', amount)

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
                            print ('count > 4')
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
                            print (price)
                            tickets.append({
                                'payee': child_id,
                                'price': price,
                                'product': product_id
                            })

                        else:
                            print ('count < 4')
                            amount += product.price
                            tickets.append({
                                'payee': child_id,
                                'price': product.price,
                                'product': product_id
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

        # Get client account and credit
        try:
            client = Client.objects.get(pk=data['payer'])
            credit = client.credit.amount
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
            methods.append({
                'amount': credit,
                'method': MethodEnum.CREDIT,
                'reference': ''
            })

            amount_expected = verify_result['amount'] - credit
            credit = 0

        
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
            pay_result['message'] = f'Incorrect amount. Expected {amount_expected} €.'
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
            pay_result['message'] = 'Failed to create an order.'
            return pay_result

        # On success Update credit
        if client:
            client.credit.amount = credit
            client.credit.date_last_mod = OrderHelper._localize(datetime.now())
            client.credit.save()
        
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
        print (verify_result)

        if soft:
            return verify_result

        # If hard
        try:
            client = Client.objects.get(pk=data['payer'])
            credit = client.credit.amount
        
            if credit > verify_result['amount']:
                verify_result['amount'] = 0

            else:
                verify_result['amount'] = verify_result['amount'] - credit
                            
        # If client does not exist return normal amount
        except:
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
