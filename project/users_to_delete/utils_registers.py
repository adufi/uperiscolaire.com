import pytz

from django.db import transaction
from datetime import datetime

from .models import User, UserAuth, UserEmail, UserPhone, UserAddress, UserEmailType, UserPhoneType, UserAddressType, Role
from .serializers import UserSerializer

"""
User registration
"""

"""
- Register a parent 
- On register/sign up page
- Lamba user
- Payload {
    email
    password1
    password2
  }
- Return user serialized data
"""
def create_parent(data):
    error = ''
    try:
        # Create auth
        auth = create_auth(data)

        # Test output
        if type(auth) is str:
            return auth

        # Create user
        # error = 'Failed to create user'
        user = User()

        # Add auth to user - Save
        # error = 'Failed to add auth'
        user.auth = auth

        # error = 'Failed to save user'
        user.save()

        # Add role
        # error = 'Failed to add role'
        role = Role.objects.get(slug='parent')
        user.roles.add(role)

        # Create email
        # error = 'Failed to add email'
        user.useremail_set.create(
            is_main=True,
            email=data['email'],
            email_type=UserEmailType.HOME.value
        )

        # error = 'Failed to serialized'
        return user

    except Role.DoesNotExist:
        return 'Role doesn\'t exist.'
        
    except:
        return ('An exception occured with error: ' + error)


"""
- Register a client 
- On payment page 
- By admin, ap_admin
- Force role to client
"""
def create_client(data):
    error = ''
    
    try:
        print('*')
        # Add client role
        data['roles'] = ['client']

        print('**')
        # Create user
        user = create_user(data, False)
        if type(user) is str:
            print (user)
            return user

        print('***')
        user.save()

        print('****')
        error = 'Serializer error'
        return user

    except:
        # print (UserSerializer(user).data)
        return f'An exception occured with error: {error}'


"""
Create an auth from a payload
Take => payload
Return => auth (without saving)
Payload {
    email
    password1
    password2
}
"""
def create_auth(data):
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
        

def _create_auth(email, password):
    return UserAuth.objects.create_user(email, password)


""" 
payload
    last_name           
    first_name          
    auth                - Optional
        email
        password1
        password2

    dob                 - Optional - Year-month-day hours:minutes:seconds
    is_active           - default true
    is_auto_password    - default false
    date_created?       - auto
    date_confirmed?     - auto
    roles []            
        role (slug)     - str
    phones              - Optional
        type
        number
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
"""
def process_user(data):
    # try:
    #     # Process email
    #     if 'emails' in data and data['emails']:
    #         email_main
    #         for email in emails:
    #             # Ensure one is_main is set to True
    #             if not has_main and len(emails) > 0:
    #                 user.emails[0].is_main = True
    #     else:
    #         if 'auth' in data:
    #             data['emails'] = [{
    #                 'is_main': True,
    #                 'email': data['auth']['email'],
    #                 'type': UserEmailType.HOME.value
    #             }]
    # except expression as identifier:
    #     pass
    pass


@transaction.atomic
def create_user(data, is_auto_password=False):
    error = ''
    print (error)
    sid = transaction.savepoint()

    try:
        # Create user
        fn = data['first_name']
        ln = data['last_name']

        error = 'Failed to create user'

        if 'dob' in data:
            dob = datetime.strptime(data['dob'], '%Y-%m-%d')
            dob = pytz.utc.localize(dob)
            user = User(
                first_name=fn,
                last_name=ln,
                dob=dob,
                is_active=True,
                is_auto_password=is_auto_password,
            )
        else:
            user = User(
                first_name=fn,
                last_name=ln,
                is_active=True,
                is_auto_password=is_auto_password
            )

        # Auth
        error = 'Failed to create auth'
        if 'auth' in data and data['auth']:
            auth = create_auth(data['auth'])
            if type(auth) is str:
                return auth

            user.auth = auth
            auth.save()

        user.save()

        """ Add secondary intels (addresses, phones) """
        # Roles
        error = 'Failed to create roles'
        if 'roles' in data:
            print (data['roles'])
            r = create_role(user, data['roles'])
            print (f'r = {r}')
            if type(r) is str:
                raise Exception(r)

        error = 'Failed to create phone'
        if 'phones' in data:
            r = create_phone(user, data['phones'])
            if type(r) is str:
                raise Exception(r)

        error = 'Failed to create emails'
        if 'emails' in data:
            r = create_email(user, data['emails'])
            if type(r) is str:
                raise Exception(r)

        error = 'Failed to create addresses'
        if 'addresses' in data:
            r = create_address(user, data['addresses'])
            if type(r) is str:
                raise Exception(r)

        transaction.savepoint_commit(sid)
        return user

    except Exception as e:
        transaction.savepoint_rollback(sid)
        print('rollback')
        if e.args:
            return e.args[0]
        return f'An exception occured with error: {error}'
    
    return 'End of function.'

    # except:
    #     transaction.savepoint_rollback(sid)
    #     print ('rollback')
    #     return f'An exception occured with error: {error}'


"""
    Allow id in payload
"""
@transaction.atomic
def create_user_migration(data, is_auto_password=False):
    error = ''
    print(error)
    sid = transaction.savepoint()

    try:
        # Create user
        if not 'id' in data:
            return 'No ID provided.'

        fn = data['first_name']
        ln = data['last_name']

        online_id = 0
        if 'online_id' in data:
            online_id = data['online_id']

        error = 'Failed to create user'

        if 'dob' in data:
            dob = datetime.strptime(data['dob'], '%Y-%m-%d')
            dob = pytz.utc.localize(dob)
            user = User(
                id=data['id'],
                first_name=fn,
                last_name=ln,
                dob=dob,
                is_active=True,
                online_id=online_id,
                is_auto_password=is_auto_password
            )
        else:
            user = User(
                id=data['id'],
                first_name=fn,
                last_name=ln,
                is_active=True,
                online_id=online_id,
                is_auto_password=is_auto_password
            )

        # Auth
        error = 'Failed to create auth'
        if 'auth' in data and data['auth']:
            auth = create_auth(data['auth'])
            if type(auth) is str:
                return auth

            user.auth = auth
            auth.save()

        user.save()

        """ Add secondary intels (addresses, phones) """
        # Roles
        error = 'Failed to create roles'
        if 'roles' in data:
            print(data['roles'])
            r = create_role(user, data['roles'])
            print(f'r = {r}')
            if type(r) is str:
                raise Exception(r)

        error = 'Failed to create phone'
        if 'phones' in data:
            r = create_phone(user, data['phones'])
            if type(r) is str:
                raise Exception(r)

        error = 'Failed to create emails'
        if 'emails' in data:
            r = create_email(user, data['emails'])
            if type(r) is str:
                raise Exception(r)

        error = 'Failed to create addresses'
        if 'addresses' in data:
            r = create_address(user, data['addresses'])
            if type(r) is str:
                raise Exception(r)

        transaction.savepoint_commit(sid)
        return user

    except Exception as e:
        transaction.savepoint_rollback(sid)
        print('rollback')
        if e.args:
            return e.args[0]
        return f'An exception occured with error: {error}'

    return 'End of function.'

    # except:
    #     transaction.savepoint_rollback(sid)
    #     print ('rollback')
    #     return f'An exception occured with error: {error}'



def create_role(user, roles):
    try:
        for role in roles:
            print (role)
            r = Role.objects.get(slug=role)
            print (r)
            user.roles.add(r)
    except Role.DoesNotExist:
            return 'Role doesn\'t exist.'
    except:
        print ('except')
        return 'An exception occured during role process.'
    print (roles)
    return True


# is_main to handle
def create_phone(user, phones):
    try:
        for phone in phones:
            type = phone['type'] if 'type' in phone else UserPhoneType.HOME.value

            p = UserPhone(
                user=user,
                phone=phone['phone'], 
                phone_type=type
            )
            p.save()
            user.userphone_set.add(p)
    except:
        return 'An exception occured during phone process.'
    return True


def create_email(user, emails):
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
            user.useremail_set.add(e)

        # Ensure one is_main is set to True
        if not has_main and len(emails) > 0:
            user.emails[0].is_main = True

    except (KeyError):
        return 'KeyError occured during email process.'
    except:
        return 'An exception occured during email process.'
    return True


def create_address(user, addresses):
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
            user.useraddress_set.add(a)

        # Ensure one is_main is set to True 
        if not has_main and len(addresses) > 0:
            user.addresses[0].is_main = True
            
    except (KeyError):
        return 'KeyError occured during address process.'
    except:
        return 'An exception occured during address process.'
    return True
