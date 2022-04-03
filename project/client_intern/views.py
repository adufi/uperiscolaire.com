import re
import json
# import pdfkit

# from weasyprint import HTML

from datetime import datetime
from django.conf import settings
from django.http import JsonResponse, Http404, HttpResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate
from django.template.loader import get_template

from rest_framework import status
from rest_framework.decorators import api_view

from users.models import User, Role, UserEmail
from users.serializers import UserSerializer, UserSerializerShort

from content.models import Content

from registration.models import Sibling, SiblingChild, SiblingIntels, Record, Family, ChildClass, ChildQuotient
from registration.serializers import RecordSerializer

from params.models import SchoolYear, Product
from params.serializers import SchoolYearSerializer

from order.models import Order, Ticket, OrderTypeEnum, Client, ClientCredit
from order.serializers import OrderSerializer, TicketSerializer

from accounting.models import Client as AClient, ClientCreditHistory as AClientCreditHistory, HistoryTypeEnum as HTE

from .utils import get_parsed_data, UsersHelper, RegistrationHelper, OrderHelper, check_authorizations, check_authorizations_v2, UnauthorizedException, NoAuthorizationFound, InvalidPayloadException, SchoolYearHelper, UserHelper, IntelHelper, SiblingHelper, RecordHelper, BadRequestException, ForbiddenException, InternalErrorException, NotFoundException, paginate

from users.decorators import login_required

regex = '[^@]+@[^@]+\.[^@]+'
# regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'

def _getLatestProducts():
    try:
        sys = SchoolYear.objects.all()
        serializer = SchoolYearSerializer(sys[0])
        return serializer
        for sy in sys:
            if sy.is_active():
                serializer = SchoolYearSerializer(sy)
                return serializer

    except SchoolYear.DoesNotExist:
        return False


def macro_get_details_by_parent(parent_id, _intels=False, _children=True):
    payload = {
        'parent': {}
    }

    user = User.objects.get(pk=parent_id)
    if not user:
        return False

    payload['parent'] = user.to_json()

    sibling = RegistrationHelper.Sibling.read_by_parent(parent_id)

    # Process school years into a dict
    school_year = None
    school_years = {}

    for s in SchoolYear.objects.all():
        if s.is_active:
            school_year = s
            continue
        school_years[s.id] = s


    if _intels:
        intel = None
        intels = {}

        for sintel in sibling.intels.all():
            if sintel.school_year == school_year.id:
                intel = sintel.to_json()
            else:
                key = school_years[sintel.school_year].date_start.year
                intels[key] = sintel.to_json()

        payload['parent']['intel'] = intel
        payload['parent']['intels'] = intels


    if _children:
        children = {}

        for schild in sibling.children.all():
            try:
                user = User.objects.get(pk=schild.child)
            except User.DoesNotExist:
                # Error - Skip
                continue
            
            child = user.to_json()
            child['record'] = None
            child['records'] = {}

            records = Record.objects.filter(child=user.id)
            for record in records:
                if record.school_year == school_year.id:
                    child['record'] = record.to_json()
                else:
                    key = school_years[record.school_year].date_start.year
                    child['records'][key] = record.to_json()

            children[user.id] = child

        payload['children'] = children

    return payload


def macro_serialize_intels(raw, school_years, active):
    intel = None
    intels = {}

    for _ in raw:
        if _.school_year == active:
            intel = _.to_json()
        else:
            key = school_years[_.school_year].date_start.year
            intels[key] = _.to_json()

    return {
        'intel': intel,
        'intels': intels
    }
    

def enhance_sibling(sibling):
    children = []

    try:
        active = SchoolYear.objects.get(is_active=True)
    except SchoolYear.DoesNotExist:
        active = None

    for sibling_child in sibling.children.all():
        # print (sibling_child)
        try:
            user = User.objects.get(pk=sibling_child.child)
            child = user.to_json()
            children.append(child)

            # print (child)

            if active:
                record = Record.objects.get(child=sibling_child.child, school_year=active.id)
                child['record'] = record.to_json()

            # print (child)

        except (User.DoesNotExist, Record.DoesNotExist):
            pass

    _ = sibling.to_json()
    _['children'] = children
    
    return _


# def redirect_home(request):
#     return redirect('home')


# Create your views here.
def redirect_children(request):
    return redirect('shop_children')


"""
COVID
"""
# def alert(request):
#     response = HttpResponse(pdf, content_type='application/pdf')
#     response['Content-Disposition'] = 'inline; filename="' + filename + '"'
#     return response
#     return render(request, 'intern/Alert.html');


"""
Login and user truc
"""
def login(request):
    return render(request, 'intern/Login.html', {})


def debug(request):
    return HttpResponse(settings.DEBUG)

"""
Account verification
"""
def verify_account(request, token):
    id = UserHelper._decode_activation_token(token)
    if type(id) is str:
        print (id)
        return HttpResponse('Lien non valide')

    try:
        user = User.objects.get(pk=id)
    except User.DoesNotExist:
        return render(request, 'intern/Login/EmailVerificationError.html')

    user.date_confirmed = datetime.now()
    user.save()
    return render(request, 'intern/Login/EmailVerificationOK.html')
    
    
def new_verification_link(request, pk):
    user = get_object_or_404(User, pk=pk)
    email = get_object_or_404(UserEmail, user=user)

    if user.date_confirmed:
        return render(request, 'intern/Login/EmailVerificationAlready.html')
        # return HttpResponse('Compte déjà confirmé')
    UserHelper.register_send_mail(request.get_host(), user.id, email.email)
    return render(request, 'intern/Login/EmailVerificationSent.html')
    # return HttpResponse('Ok')


"""
Password forgotten?
"""
""" Apply password change """
def change_password(request, token=''):
    if not token:
        return render (request, 'intern/Login/ChangePassword.html', {'status': 1, 'message': 'Token invalide. Veuillez recommencer la procédure.'})

    id = UserHelper._decode_change_password_token(token)
    if type(id) is str:
        return render (request, 'intern/Login/ChangePassword.html', {
            'status': 2, 
            'message': 'Token invalide. Veuillez recommencer la procédure.',
            'error': id
        })

    try:
        user = User.objects.get(pk=id)
        if not hasattr(user, 'auth'):
            return render (request, 'intern/Login/ChangePassword.html', {
                'status': 1, 
                'message': 'Cet utilisateur n\'a aucun identifiants associés.',
            })
    except User.DoesNotExist:
        return render (request, 'intern/Login/ChangePassword.html', {
            'status': 1, 
            'message': 'L\'utilisateur est introuvable.',
        })

    if request.method == 'GET':
        return render (request, 'intern/Login/ChangePassword.html', {'status': 0})

    elif request.method == 'POST':
        password1 = request.POST.get('password1', False)
        password2 = request.POST.get('password2', False)

        if not password1 or not password2:
            return render (request, 'intern/Login/ChangePassword.html', {
                'status': 0, 
                'message': 'Les mots de passe sont invalides.',
            })

        if password1 != password2:
            return render (request, 'intern/Login/ChangePassword.html', {
                'status': 0, 
                'message': 'Les mots de passe sont différents.',
            })

        user.auth.set_password(password1)
        user.auth.save()
        return render (request, 'intern/Login/ChangePassword.html', {
            'status': 3
        })

    return render (request, 'intern/Login/ChangePassword.html', {
        'status': 1, 
        'message': 'Une erreur est survenue lors de la procédure.',
    })


""" Prompt user to enter his email - Send link if account is valid """
def password_forgotten(request, email=''):
    if not email:
        return render (request, 'intern/Login/PasswordForgotten.html')

    # Test email
    if re.search(regex, email):
        try:
            user = User.objects.get(auth__email=email)
            UserHelper.change_password(request.get_host(), user.id, email)
            return render (request, 'intern/Login/PasswordForgottenOK.html')
        except User.DoesNotExist:
            return render (request, 'intern/Login/PasswordForgotten.html', {'error': 'L\'utilisateur est introuvable.'})
    else:
        return render (request, 'intern/Login/PasswordForgotten.html', {'error': 'L\'adresse email est incorrect.'})



"""

"""
""" Home page """
# def home(request):
#     # u = User.objects.get(id=81)
#     # print (request.get_host())
#     return render(request, 'intern/Home.html', {})


def user_user(request, pk=0):
    """
    Return
    ------
    parent {
        parent {}
        children {
            `user profile`
            
        }
    }
    """
    return render(request, 'intern/User/User.html', {'pk': pk})

    # Check authentication
    try:
        if request.user.is_authenticate:
            print ('user is_authenticate')
        else:
            raise Exception('User is not authenticated')
    except Exception as e:
        log = ''
        if e.args:
            log = e.args[0]
        return render(request, 'intern/User/User.html', {
            'log': log,
            'status': 'Failure',
            'message': 'Vous n\'êtes pas autoriser à consulter cette page.'
        })

    # Check authorization


    # if not check_authorizations(request.headers, ['admin', 'is_superuser']):
    try:
        if not check_authorizations(request.headers, ['admin', 'is_superuser', 'parent']):
            return render(request, 'intern/User/User.html', {'message': 'Vous n\'êtes pas autoriser à consulter cette page.'})

        id = check_authorizations(request.headers, ['parent'])
        if id:
            pk = id
    except Exception as e:
        if e.args:
            return render(request, 'intern/User/User.html', {'message': e.args[0]})
        return render(request, 'intern/User/User.html', {'message': 'Une erreur est survenue.'})

    # user = UsersHelper.user_read(3)
    user = User.objects.get(pk=11)
    if not user:
        return render(request, 'intern/User/User.html', {'user': {}})
    # return render(request, 'intern/User/User.html', {'user': user.to_json()})

    if user.roles.filter(slug='parent'):
        parent = user.to_json()
        # print (parent)

        payload = macro_get_details_by_parent(11, _intels=True, _children=True)
        
        return render(request, 'intern/User/User.html', {'parent': user.to_json(), 'payload': payload})

    if user.roles.filter(slug='child'):
        child = user.to_json()
        return render(request, 'intern/User/User.html', {'child': child})

    return render(request, 'intern/User/User.html', {'user': user.to_json()})


def user_family(request, pk):
    """
    Return
    ------
    parent {
        parent {}
        children {
            `user profile`
            
        }
    }
    """
    return render(request, 'intern/User/Family.html', {'pk': pk})


def user_demo(request):
    return render(request, 'intern/User/Demo.html', {})


def user_record(request, child=0, record=0):
    _ = Content.objects.filter(name='Record').first()
    return render(request, 'intern/User/Record.html', {
        'child': child,
        'record': record,
        'content': _
    })


def user_record_pdf(request, child, record):
    status = False
    message = ''

    try:
        _child = User.objects.get(pk=child)
        _record = Record.objects.get(pk=record)

        sibling = Sibling.objects.get(children__child=child)
        _intel = sibling.intels.filter(school_year=_record.school_year)
        if _intel:
            intel = _intel.first()

        _parent = User.objects.get(pk=sibling.parent)

        status = True
    except User.DoesNotExist:
        message = 'User does not exist'

    except Record.DoesNotExist:
        message = 'Record does not exist'
        pass

    except Sibling.DoesNotExist:
        message = 'Sibling does not exist'
        pass
    
    # try:
    # except User.DoesNotExist:
    #     pass
    
    if status:
        template = get_template('intern/Record/Print.html')
        html = template.render({
            'status': status,
            'child': _child,
            'parent': _parent,
            'record': _record,
            'intel': intel,
            'sibling': sibling
        })
    
    else:
        template = get_template('intern/Record/Print.html')
        html = template.render({
            'status': status,
            'message': message
        })

    # pdf = None
    # pdf = pdfkit.from_string(html, False)
    # pdf = HTML(string=html, base_url=request.build_absolute_uri()).write_pdf()
    # filename = 'fiche_inscription_2020-2021.pdf'

    # response = HttpResponse(pdf, content_type='application/pdf')
    # response['Content-Disposition'] = 'inline; filename="' + filename + '"'
    # return response
    return HttpResponse('Ok')


def user_record_print(request, child, record):
    status = False
    message = ''

    try:
        _child = User.objects.get(pk=child)
        _record = Record.objects.get(pk=record)

        sibling = Sibling.objects.get(children__child=child)
        _intel = sibling.intels.filter(school_year=_record.school_year)
        if _intel:
            intel = _intel.first()

        _parent = User.objects.get(pk=sibling.parent)

        status = True
    except User.DoesNotExist:
        message = 'User does not exist'

    except Record.DoesNotExist:
        message = 'Record does not exist'
        pass

    except Sibling.DoesNotExist:
        message = 'Sibling does not exist'
        pass
    
    # try:
    # except User.DoesNotExist:
    #     pass
    
    if status:
        return render(request, 'intern/Record/Print.html', {
            'status': status,
            'child': _child,
            'parent': _parent,
            'record': _record,
            'intel': intel,
            'sibling': sibling
        })
    
    else:
        return render(request, 'intern/Record/Print.html', {
        'status': status,
        'message': message
    })



""" 
MNGT template routes
"""

def mngt_user(request, pk):
    return render(request, 'intern/Mngt/User.html')

def mngt_users(request):
    return render(request, 'intern/Mngt/Users.html')


"""
PARAMS Routes
"""

@api_view(['GET'])
def api_params_schoolyear(request, pk=0):
    response_object = {
        'status': 'Failure'
    }

    if request.method == 'GET':
        try:
            r = SchoolYearHelper.read(pk)
        except SchoolYear.DoesNotExist:
            response_object['message'] = 'SchoolYear does not exist'
            return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

        response_object['status'] = 'Success'
        if pk:
            response_object['school_year'] = r
        else:
            response_object['school_years'] = r

        return JsonResponse(response_object, status=status.HTTP_200_OK)
        

    return JsonResponse(response_object, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def api_params_product(request):
    response_object = {
        'status': 'Failure'
    }

    try:
        sy = SchoolYear.objects.get(is_active=True)
    except SchoolYear.DoesNotExist:
        response_object['message'] = 'Aucune année scolaire active.'
    except SchoolYear.MultipleObjectsReturned:
        response_object['message'] = 'Plusieurs années scolaires actives trouvées.'
    
    if 'message' in response_object:
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    response_object['status'] = 'Success'
    response_object['school_year'] = sy.to_json()

    # sy_2 = SchoolYear.objects.get(pk=22)

    response_object['products'] = [x.to_json() for x in sy.products.all()]
    return JsonResponse(response_object, status=status.HTTP_200_OK)


"""
USER Routes
"""


def user_users(request):
    return render(request, 'intern/User/Users.html')


"""
USER API Routes
"""

""" Get a single user - id for admin - token for casual """
@api_view(['GET'])
def api_user_read_profile(request, pk=0):
    """
    Return
    ------
    parent {
        parent {}
        children {
            `user profile`
            
        }
    }
    """
    response_object = {
        'status': 'Failure'
    }

    # Check authentication
    # Check authorization
    try:
        check = check_authorizations(request.headers, ['admin', 'is_superuser', 'parent'])
        if not check:
            response_object['message'] = 'Vous n\'êtes pas autorisé à consulter cette page.'
            return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

        # Prevent id to be invalid
        if pk < 0:
            response_object['message'] = 'Clé primaire invalide.'
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        # Return self id
        elif not pk:
            pk = check['id']

        else:
            # Prevent parent user to access other users data
            if 'parent' in check['role']:
                if pk == check['role']:
                    pass
                else:
                    # Check parent sibling
                    children = Sibling.objects.filter(parent=check['id'], children__child=pk)
                    if not children:
                        response_object['message'] = 'Vous n\'êtes pas autorisé à consulter cette page.'
                        return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

    
    except Exception as e:
        response_object['message'] = 'Une erreur est survenue.'
        if e.args:
            response_object['message'] = e.args[0]
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    # user = UsersHelper.user_read(3)
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        response_object['message'] = 'User does not exist'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    if user.roles.filter(slug='parent'):
        parent = user.to_json()
        # print (parent)

        # payload = macro_get_details_by_parent(pk, _intels=True, _children=True)
        
        response_object['user'] = parent
        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    response_object['user'] = user.to_json()
    response_object['status'] = 'Success'
    return JsonResponse(response_object, status=status.HTTP_200_OK)



    # if user.roles.filter(slug='child'):
    #     child = user.to_json()
    #     return render(request, 'intern/User/User.html', {'child': child})

    # return render(request, 'intern/User/User.html', {'user': user.to_json()})


@api_view(['GET'])
def api_user_read_all(request):
    """
    Parameters
    ----------
    GET
        id
        roles
        dob
        slug
        last_name
        first_name
    """
    response_object = {
        'status': 'Failure'
    }

    try:
        check = check_authorizations(request.headers, ['admin', 'is_superuser'])
        if not check:
            response_object['message'] = 'Vous n\'êtes pas autorisé à consulter cette page.'
            return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)    
    except Exception as e:
        response_object['message'] = 'Une erreur est survenue.'
        if e.args:
            response_object['message'] = e.args[0]
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    _users = UsersHelper.users_read(request)
    if not _users:
        response_object['message'] = 'User does not exist'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    response_object['status'] = 'Success'

    if type(_users) is User:
        response_object['user'] = _users.to_json()
    else:
        response_object.update(_users)
    
    return JsonResponse(response_object, status=status.HTTP_200_OK)


@api_view(['POST'])
def api_auth_token(request):
    response_object = {
        'status': 'Failure',
        'message': 'Payload invalide.'
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
            response_object['message'] = 'Identifiants invalides.'
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        response_object['token'] = auth.token
        response_object['status'] = 'Success'

        # if hasattr(auth, 'user'):
        #     response_object['user'] = auth.user.to_json()
        #     # serializer = UserSerializer(auth.user)
        #     # response_object['user'] = serializer.data
            
        # else:
        #     response_object['user'] = {
        #         'auth': {'email': auth.email}
        #     }            

        del response_object['message']
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except Exception as e:
        if e.args:
            response_object['message'] = 'Payload invalide avec erreur: {}'.format(e.args[0])
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


"""
As parent
---------
    GET /api/user/              - FORBIDDEN
    GET /api/user/<pk>          - Get user by id (self/children)
    POST /api/user/             - Create intel for parent - Last school year
    PUT /api/user/<pk>          - Update self or children

As admin
---------
    GET /api/user/              - List users
    GET /api/user/<pk>          - Get user by id (self/children)
    POST /api/user/             - Create an user
    PUT /api/user/<pk>          - Update user by pk
"""
@api_view(['GET', 'POST', 'PUT'])
def api_user(request, pk=0):
    response_object = {
        'status': 'Failure'
    }

    def macro_process_error (e):
        if e.args:
            response_object['message'] = e.args[0]

    try:
        check = check_authorizations_v2(request.headers, ['admin', 'is_superuser', 'parent'])

        is_admin = False
        sibling = None

        if 'admin' in check['role']:
            is_admin = True

        if 'parent' in check['role']:
            sibling = Sibling.objects.get(parent=check['id'])

        if request.method == 'GET':
            _ = UserHelper.read(sibling, pk, is_admin, request.GET)
            if is_admin and not pk:
                if type(_) is dict:
                    response_object['users'] = _
                else:
                    response_object['users'] = [x.to_json() for x in _]
            else:
                response_object['user'] = _.to_json()

                # if check['id'] == _.id:
                try:
                    credit = ClientCredit.objects.get(client__pk=_.id)
                    response_object['user']['credit'] = credit.amount
                except ClientCredit.DoesNotExist:
                    response_object['user']['credit'] = 0

        # POST
        # Only for child
        # Parent ID required on admin request
        elif request.method == 'POST':
            if not request.data:
                response_object['message'] = 'No data found'
                return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

            data = get_parsed_data(request.data)

            user = UserHelper.create(sibling, data, is_admin)
            response_object['user'] = user.to_json()

        # PUT
        elif request.method == 'PUT':
            if not pk:
                response_object['message'] = 'Please specify an ID on update'
                return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

            if not request.data:
                response_object['message'] = 'No data found'
                return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

            data = get_parsed_data(request.data)

            user = UserHelper.update(sibling, pk, data, is_admin)
            response_object['user'] = user.to_json()

        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except (NoAuthorizationFound, UnauthorizedException, UserHelper.Unauthorized) as e:
        response_object['message'] = 'Vous n\'êtes pas autorisé à consulter cette page.'
        if e.args:
            response_object['message'] += ' ({})'.format(e.args[0])
        # print (response_object)
        return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

    except Sibling.DoesNotExist:
        response_object['message'] = 'Sibling does not exist'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND) 

    except Sibling.MultipleObjectsReturned:
        response_object['message'] = 'Sibling returned more than 1 object'
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except UserHelper.BadRequestException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except UserHelper.ForbiddenException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    except UserHelper.NotFoundException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except UserHelper.InternalErrorException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        response_object['message'] = 'Une erreur est survenue.'
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except User.DoesNotExist:
        response_object['message'] = 'User does not exist'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND) 

    except UserHelper.SiblingNotSet:
        response_object['message'] = 'Sibling is not set'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND) 

    except SiblingIntels.DoesNotExist:
        response_object['message'] = 'Intel does not exist'
        if 'parent' in check['role']:
            response_object['message'] = 'Intel is not bound to parent'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    # create_intel
    except InvalidPayloadException as e:
        response_object['message'] = 'Invalid payload'
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except SchoolYear.DoesNotExist:
        response_object['message'] = 'Registration closed for this period'
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


""" Search users by filters  """
"""
Filters
    names
    roles
    school
    quotients
"""
@api_view(['GET'])
def api_userquery(request):
    response_object = {
        'status': 'Failure'
    }

    def macro_process_error (e):
        if e.args:
            response_object['message'] = e.args[0]

    try:
        check = check_authorizations_v2(request.headers, ['admin', 'is_superuser'])

        is_admin = False
        sibling = None

        if 'admin' in check['role']:
            is_admin = True

        if 'parent' in check['role']:
            sibling = Sibling.objects.get(parent=check['id'])

        if request.method == 'GET':
            name_search = True

            school = request.GET.get('school', 'All')
            quotient_1 = int(request.GET.get('quotient_1', -1))
            quotient_2 = int(request.GET.get('quotient_2', -1))

            print (school)
            print (quotient_1)
            print (quotient_2)

            users = User.objects.all()
            filtered = users

            if school != 'All':
                print (school)
                name_search = False

                SCHOOLS = [
                    'PRES',
                    'EM',
                    'BDP',
                    'CHAP',
                    'DUR',
                    'GOND',
                    'MDO',
                    'HM',
                    'JM',
                    'AUTRES',
                ] 

                if school in SCHOOLS:
                    print (school)
                    records = Record.objects.filter(school=school, school_year=24)

                    children_ids = [_.child for _ in records]
                    print (len(children_ids))

                    siblings = Sibling.objects.filter(children__child__in=children_ids)

                    parents_ids = [_.parent for _ in siblings]
                    print (len(parents_ids))

                    filtered = filtered.filter(pk__in=children_ids+parents_ids)



            intels = None
            if quotient_1 != -1:
                name_search = False
                intels = SiblingIntels.objects.filter(quotient_1=quotient_1, school_year=24)

            if quotient_2 != -1:
                name_search = False
                if intels:
                    intels = intels.filter(quotient_2=quotient_2)
                else:
                    intels = SiblingIntels.objects.filter(quotient_2=quotient_2)




            # User filtering
            # ...
            # Roles
            roles = request.GET.get('roles', '')
            if roles and name_search:
                for role in roles.split(','):
                    filtered = filtered.filter(roles__slug=role)

            # Names
            names = request.GET.get('names', '')
            if names and name_search:
                filtered = UserHelper.read_search_name(filtered, names)


            def processData(data):
                # print (data[0])
                return [x.to_json() for x in data]

            page = int(request.GET.get('page', 1))
            response_object['users'] = paginate(filtered, page, processData)


        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except (NoAuthorizationFound, UnauthorizedException, UserHelper.Unauthorized) as e:
        response_object['message'] = 'Vous n\'êtes pas autorisé à consulter cette page.'
        if e.args:
            response_object['message'] += ' ({})'.format(e.args[0])
        # print (response_object)
        return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

    except Sibling.DoesNotExist:
        response_object['message'] = 'Sibling does not exist'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND) 

    except Sibling.MultipleObjectsReturned:
        response_object['message'] = 'Sibling returned more than 1 object'
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except UserHelper.BadRequestException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except UserHelper.ForbiddenException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    except UserHelper.NotFoundException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except UserHelper.InternalErrorException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        response_object['message'] = 'Une erreur est survenue.'
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except User.DoesNotExist:
        response_object['message'] = 'User does not exist'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND) 

    except UserHelper.SiblingNotSet:
        response_object['message'] = 'Sibling is not set'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND) 

    except SiblingIntels.DoesNotExist:
        response_object['message'] = 'Intel does not exist'
        if 'parent' in check['role']:
            response_object['message'] = 'Intel is not bound to parent'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    # create_intel
    except InvalidPayloadException as e:
        response_object['message'] = 'Invalid payload'
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except SchoolYear.DoesNotExist:
        response_object['message'] = 'Registration closed for this period'
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


""" List users """
@api_view(['GET'])
@login_required(['admin', 'is_superuser', 'parent'])
def api_users(request):
    response_object = {'status': 'Failure'}


""" Get user names by pk """
@api_view(['GET'])
@login_required(['admin', 'is_superuser', 'parent'])
def api_user_names(request):
    response_object = {'status': 'Failure'}

    is_admin = False
    sibling = None
    
    if 'admin' in request.META['check']['role']:
        is_admin = True

    pk = request.GET.get('pk', 0)
    pk_in = request.GET.get('pk_in', 0)

    if pk:
        if not is_admin:
            if pk != request.META['check']['id']:
                response_object['message'] = 'Vous n\'êtes pas autorisé à récupérer ces ressources.'
                return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            response_object['message'] = 'Utilisateur introuvable.'
            return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

        response_object['status'] = 'Success'
        response_object['user'] = json.dumps({'first_name': user.first_name, 'last_name': user.last_name})
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    if pk_in:
        if not is_admin:
            response_object['message'] = 'Vous n\'êtes pas autorisé à récupérer ces ressources.'
            return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

        to_list = lambda s: s.split(',')

        users = User.objects.filter(pk__in=to_list(pk_in))

        response_object['status'] = 'Success'
        response_object['users'] = [{'id': user.id, 'first_name': user.first_name, 'last_name': user.last_name} for user in users]
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    response_object['message'] = 'Impossible de traiter les arguments.'
    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


"""
As parent
---------
    GET /api/sibling/              - FORBIDDEN
    GET /api/sibling/<pk>          - Get sibling by id
    GET /api/sibling/?child=<id>   - Get sibling by child id
    GET /api/sibling/?parent=<id>  - Get sibling by parent id
    POST /api/sibling/             - Create intel for parent - Last school year
    PUT /api/sibling/              - Update self or children

As admin
---------
    GET /api/sibling/              - List siblings
    GET /api/sibling/<pk>          - Get sibling by id (self/children)
    POST /api/sibling/             - Create an sibling
    PUT /api/sibling/<pk>          - Update sibling by pk
"""
@api_view(['GET', 'POST', 'PUT'])
def api_sibling(request, pk=0):
    response_object = {
        'status': 'Failure'
    }

    def macro_process_error (e):
        if e.args:
            response_object['message'] = e.args[0]

    try:
        check = check_authorizations(request.headers, ['admin', 'is_superuser', 'parent'])

        is_admin = False
        sibling = None

        if 'admin' in check['role']:
            is_admin = True

        if 'parent' in check['role']:
            sibling = Sibling.objects.get(parent=check['id'])

        if request.method == 'GET':
            _ = SiblingHelper.read(sibling, pk, is_admin, request.GET)
            if type(_) == Sibling:
                response_object['sibling'] = enhance_sibling(_)
            else:
                response_object['siblings'] = [enhance_sibling(x) for x in _]

        # PUT
        # elif request.method == 'PUT':
        #     if not pk:
        #         response_object['message'] = 'Please specify an ID on update'
        #         return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        #     if not request.data:
        #         response_object['message'] = 'No data found'
        #         return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        #     data = get_parsed_data(request.data)

        #     user = UserHelper.update(sibling, pk, data, is_admin)
        #     response_object['user'] = user.to_json()

        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except (NoAuthorizationFound, UnauthorizedException, UserHelper.Unauthorized) as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

    except Sibling.DoesNotExist:
        response_object['message'] = 'Sibling does not exist'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND) 

    except Sibling.MultipleObjectsReturned:
        response_object['message'] = 'Sibling returned more than 1 object'
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except SiblingHelper.BadRequestException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except SiblingHelper.ForbiddenException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    except SiblingHelper.NotFoundException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except SiblingHelper.InternalErrorException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        response_object['message'] = 'Une erreur est survenue.'
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


"""
As parent
---------
    GET /api/record/              - FORBIDDEN
    GET /api/record/<pk>          - Get record by id (self/children)
    GET /api/record/?child=<id>   - Get record by child id
    GET /api/record/?parent=<id>  - Get record by parent id
    POST /api/record/             - Create record for parent - Last school year
    PUT /api/record/<pk>          - Update record if last SY and not verified

As admin
---------
    GET /api/record/              - List records
    GET /api/record/<pk>          - Get record by id
    GET /api/record/?child=<id>   - Get record by child id
    GET /api/record/?parent=<id>  - Get record by parent id
    POST /api/record/             - Create an record
    PUT /api/record/<pk>          - Update record
"""
@api_view(['GET', 'POST', 'PUT'])
def api_record(request, pk=0):
    response_object = {
        'status': 'Failure'
    }

    def macro_process_error (e):
        if e.args:
            response_object['message'] = e.args[0]

    try:
        check = check_authorizations(request.headers, ['admin', 'is_superuser', 'parent'])

        is_admin = False
        sibling = None

        if 'admin' in check['role']:
            is_admin = True

        if 'parent' in check['role']:
            sibling = Sibling.objects.get(parent=check['id'])

        if request.method == 'GET':
            _ = RecordHelper.read(sibling, pk, is_admin, request.GET)
            if type(_) == Record:
                response_object['record'] = _.to_json()
            else:
                response_object['records'] = [x.to_json() for x in _]

        elif request.method == 'POST':
            if not request.data:
                response_object['message'] = 'No data found'
                return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

            data = get_parsed_data(request.data)

            record = RecordHelper.create(sibling, data, is_admin)
            
            response_object['record'] = record.to_json()

        # PUT
        elif request.method == 'PUT':
            if not pk:
                response_object['message'] = 'Please specify an ID on update'
                return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

            if not request.data:
                response_object['message'] = 'No data found'
                return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

            data = get_parsed_data(request.data)

            user = RecordHelper.update(sibling, pk, data, is_admin)
            response_object['record'] = user.to_json()

        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except (NoAuthorizationFound, UnauthorizedException, UserHelper.Unauthorized) as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)

    except Sibling.DoesNotExist:
        response_object['message'] = 'Sibling does not exist'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND) 

    except Sibling.MultipleObjectsReturned:
        response_object['message'] = 'Sibling returned more than 1 object'
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except BadRequestException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except ForbiddenException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    except NotFoundException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except InternalErrorException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        response_object['message'] = 'Une erreur est survenue.'
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


"""
NOTE
----
Sibling should be created when a parent register

As parent
---------
    GET /api/user/intel/                - Get every intels for payload ID
    GET /api/user/intel/<pk>            - Get a given intel if it BELONGS to parent
    GET /api/user/intel/?parent=<pk>    - Get every intels for a parent ID
    POST /api/user/intel/               - Create intel - override parent ID and school year
    PUT /api/user/intel/                - Update active intel
    PUT /api/user/intel/<pk>            - Update intel by pk (if active/if sibling)

As admin
---------
    GET /api/user/intel/                - Get every intels for payload ID
    GET /api/user/intel/<pk>            - Get a given intel for a pk
    GET /api/user/intel/?all=true       - Get every intels
    GET /api/user/intel/?parent=<pk>    - Get every intels for a parent ID
    POST /api/user/intel/               - Create an intel
    PUT /api/user/intel/                - Update active intel
    PUT /api/user/intel/<pk>            - Update intel by pk
"""
@api_view(['GET', 'POST', 'PUT'])
def api_user_intel(request, pk=0):
    response_object = {
        'status': 'Failure'
    }

    def macro_process_error (e):
        if e.args:
            response_object['message'] = e.args[0]

    try:
        check = check_authorizations(request.headers, ['admin', 'is_superuser', 'parent'])

        # if 'parent' in check['role']:
        #     sibling = Sibling.objects.get(parent=check['id'])

            # if request.method == 'GET':
            #     # Get every intels
            #     if pk == 0:
            #         # UPDATE - Need work
            #         # 
            #         parent_id = request.GET.get('parent', 0)
            #         if parent_id:
            #             intels = SiblingIntels.objects.filter(sibling__parent=parent_id)
            #         else:
            #             intels = SiblingIntels.objects.all()

            #         # intels = sibling.intels.all()
            #         response_object['intels'] = [x.to_json() for x in intels]

            #     else:
            #         intel = sibling.intels.get(pk=pk)
            #         response_object['intel'] = intel.to_json()

            # elif request.method == 'POST':
            #     if not request.data:
            #         response_object['message'] = 'No data found'
            #         return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

            #     data = get_parsed_data(request.data)

            #     intel = RegistrationHelper.create_intel(sibling, data, False)
            #     if not intel:
            #         response_object['message'] = 'Intel already exist'
            #         return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

            #     response_object['intel'] = intel.to_json()

        # else:
        #     if request.method == 'GET':
        #         if pk == 0:
        #             # UPDATE - Need work
        #             # 
        #             parent_id = request.GET.get('parent', 0)
        #             if parent_id:
        #                 intels = SiblingIntels.objects.filter(sibling__parent=parent_id)
        #             else:
        #                 intels = SiblingIntels.objects.all()
        #             response_object['intels'] = [x.to_json() for x in intels]
        #         else:
        #             intel = SiblingIntels.objects.get(pk=pk)
        #             response_object['intel'] = intel.to_json()

            # elif request.method == 'POST':
            #     if not request.data:
            #         response_object['message'] = 'No data found'
            #         return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

            #     data = get_parsed_data(request.data)

            #     # Find parent ID
            #     parent_id = data.get('parent_id', check['id'])

            #     sibling = Sibling.objects.get(parent=parent_id)

            #     intel = RegistrationHelper.create_intel(sibling, data, True)
            #     if not intel:
            #         response_object['message'] = 'Intel already exist'
            #         return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

            #     response_object['intel'] = intel.to_json()


        is_admin = False
        sibling = None

        if 'admin' in check['role']:
            is_admin = True

        if 'parent' in check['role']:
            sibling = Sibling.objects.get(parent=check['id'])

        print (check['id'])
        print (sibling)

        if request.method == 'GET':
            if pk:
                intel = IntelHelper.read(sibling, pk, is_admin, request.GET)
                response_object['intel'] = intel.to_json()
            else:
                intels = IntelHelper.read(sibling, pk, is_admin, request.GET)
                response_object['intels'] = [x.to_json() for x in intels]
            
        elif request.method == 'POST':

            if not request.data:
                response_object['message'] = 'No data found'
                return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

            data = get_parsed_data(request.data)

            if is_admin:
                sibling = Sibling.objects.get(parent=data.get('parent_id', check['id']))
            
            intel = IntelHelper.create(sibling, data, is_admin)

            response_object['intel'] = intel.to_json()
            
        elif request.method == 'PUT':

            if not request.data:
                response_object['message'] = 'No data found'
                return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

            data = get_parsed_data(request.data)

            intel = IntelHelper.update(sibling, data, pk, is_admin)

            response_object['intel'] = intel.to_json()

        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except (NoAuthorizationFound, UnauthorizedException, IntelHelper.Unauthorized) as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)
        
    except Sibling.DoesNotExist:
        response_object['message'] = 'Famille introuvable.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND) 

    except Sibling.MultipleObjectsReturned:
        response_object['message'] = 'Sibling returned more than 1 object'
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except SiblingIntels.DoesNotExist:
        response_object['message'] = 'Informations familliales introuvable.'
        if 'parent' in check['role']:
            response_object['message'] = 'Informations non liées au parent'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    # create_intel
    except InvalidPayloadException as e:
        response_object['message'] = 'Payload invalide.'
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except SchoolYear.DoesNotExist:
        response_object['message'] = 'Inscription fermée pour cette période'
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    except SchoolYear.MultipleObjectsReturned:
        response_object['message'] = 'School Year returned more than 1 object'
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except IntelHelper.BadRequestException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    except IntelHelper.ForbiddenException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    except IntelHelper.NotFoundException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    except IntelHelper.InternalErrorException as e:
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        response_object['message'] = 'Une erreur est survenue.'
        macro_process_error(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)


"""

"""
@api_view(['GET'])
def api_order(request, pk=0):
    response_object = {
        'status': 'Failure'
    }

    try:
        check = check_authorizations_v2(request.headers, ['admin', 'is_superuser', 'parent'])

        is_admin = False
        sibling = None

        if 'admin' in check['role']:
            is_admin = True

        if 'parent' in check['role']:
            sibling = Sibling.objects.get(parent=check['id'])

        if request.method == 'GET':

            pk = request.GET.get('pk')
            if pk:
                try:
                    order = Order.objects.get(pk=pk)
                except Order.DoesNotExist:
                    response_object['message'] = 'Reçu introuvable'
                    return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)
                
                response_object['order'] = OrderSerializer(order).data

            else:
                all = Order.objects.all().order_by('-date')
                filtered = all
                
                date_end = request.GET.get('date_end', 0)
                date_start = request.GET.get('date_start', 0)
                payer_pk = request.GET.get('payer', 0)
                caster_pk = request.GET.get('caster', 0)

                if date_start:
                    filtered = filtered.filter(date__gte=date_start)

                if date_end:
                    filtered = filtered.filter(date__lte=date_end)

                if caster_pk:
                    filtered = filtered.filter(caster=caster_pk)

                if payer_pk:
                    filtered = filtered.filter(payer=payer_pk)

                def processData(data):
                    # print (data[0])
                    return OrderSerializer(data, many=True).data

                page = int(request.GET.get('page', 1))
                response_object['orders'] = paginate(filtered, page, processData)
            
        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    except (NoAuthorizationFound, UnauthorizedException, UserHelper.Unauthorized) as e:
        response_object['message'] = 'Vous n\'êtes pas autorisé à consulter cette page.'
        if e.args:
            response_object['message'] += ' ({})'.format(e.args[0])
        # print (response_object)
        return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)



""" Obsolete """
@api_view(['POST'])
def api_user_update(request):
    response_object = {
        'status': 'Failure'
    }
    if not request.data:
        response_object['message'] = 'Invalid payload'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    roles = Role.objects.filter(user__pk=data.get('id', 0))
    if not roles:
        response_object['message'] = 'Invalid user'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    # if roles.filter(slug=):


    user = UsersHelper.update_user(data)
    if type(user) is str:
        response_object['message'] = user
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)
    
    response_object['status'] = 'Success'
    response_object['user'] = user.to_json()
    return JsonResponse(response_object, status=status.HTTP_200_OK)


@api_view(['POST'])
def api_user_create_child(request):
    response_object = {
        'status': 'Failure'
    }
    if not request.data:
        response_object['message'] = 'Invalid payload'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    # if 'Authorization' in request.headers:
    #     print (request.headers.get('Authorization'))
    # else:
    #     print ('No headers')

    data = get_parsed_data(request.data)

    user = UsersHelper.create_child(data)
    if type(user) is str:
        response_object['message'] = user
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)
    
    response_object['status'] = 'Success'
    response_object['user'] = user.to_json()
    return JsonResponse(response_object, status=status.HTTP_200_OK)


@api_view(['POST'])
def api_user_delete_child(request):
    response_object = {
        'status': 'Failure'
    }
    if not request.data:
        response_object['message'] = 'Invalid payload'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    user = UsersHelper.delete_child(data)
    if type(user) is str:
        response_object['message'] = user
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)
    
    response_object['status'] = 'Success'
    return JsonResponse(response_object, status=status.HTTP_200_OK)


@api_view(['POST'])
def api_user_update_sibling_child(request):
    response_object = {
        'status': 'Failure'
    }
    if not request.data:
        response_object['message'] = 'Invalid payload'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    user = UsersHelper.update_child_sibling(data)
    if type(user) is str:
        response_object['message'] = user
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)
    
    response_object['status'] = 'Success'
    return JsonResponse(response_object, status=status.HTTP_200_OK)




"""
SHOP Routes
"""
# Old route - closed
def shop(request):
    return render(request, 'intern/Shop.html', {})

# Old route - closed
def shop_shop(request):
    return render(request, 'intern/Shop/Shop_Shop_Updated.html', {})

def shop_demo(request):
    # Assuming "child test" ID is 23
    sibling = RegistrationHelper.sibling_read_full(23)

    if type(sibling) is str:
        return render(request, 'intern/Shop/Shop_Demo.html', {'sibling': {}, 'message': sibling})

    # Get client data
    client = OrderHelper.get_client_data(sibling['parent']['id'])
    sibling['parent']['client'] = client

    for key in sibling['children']:
        child = sibling['children'][key]
        tickets = OrderHelper.Ticket.read_from_child(child['id'])
        child['tickets'] = TicketSerializer(tickets, many=True).data

    return render(request, 'intern/Shop/Shop_Demo.html', {
        'sibling': json.dumps(sibling),
        'products': json.dumps(_getLatestProducts().data['product'])
    })


def shop_children(request):
    return render(request, 'intern/Shop/Shop_Children.html')
    children = User.objects.filter(roles__slug='child')
    return render(request, 'intern/Shop_Children.html', {'children': children})
    

def shop_summary(request, child):
    return render(request, 'intern/Shop_Summary.html')
    sibling = RegistrationHelper.sibling_read_full(child)

    if type(sibling) is str:
        return render(request, 'intern/Shop_Summary.html', {'sibling': {}, 'message': sibling})

   # Get client data
    client = OrderHelper.get_client_data(sibling['parent']['id'])
    if client:
        sibling['parent']['client'] = client

    for key in sibling['children']:
        child = sibling['children'][key]
        tickets = OrderHelper.Ticket.read_from_child(child['id'])
        child['tickets'] = TicketSerializer(tickets, many=True).data

    return render(request, 'intern/Shop_Summary.html', {
        'sibling': json.dumps(sibling),
        'products': json.dumps(_getLatestProducts().data['product'])
    })


def shop_shop_child(request, child):
    return render(request, 'intern/Shop/Shop_Shop_Updated.html')

    sibling = RegistrationHelper.sibling_read_full(child)

    if type(sibling) is str:
        return render(request, 'intern/Shop_Shop.html', {'sibling': {}, 'message': sibling})

    # Get client data
    client = OrderHelper.get_client_data(sibling['parent']['id'])
    if client:
        sibling['parent']['client'] = client

    # Get tickets
    for key in sibling['children']:
        child = sibling['children'][key]
        tickets = OrderHelper.Ticket.read_from_child(child['id'])
        child['tickets'] = TicketSerializer(tickets, many=True).data

    return render(request, 'intern/Shop_Shop.html', {
        'sibling': json.dumps(sibling),
        'products': json.dumps(_getLatestProducts().data['product'])
    })


"""

"""
def shop_view(request, parent):
    return render(request, 'intern/Shop/Shop_View.html')



"""
USERS API Routes
"""
@api_view(['GET'])
def api_user_get(request, id):
    response_object = {
        'status': 'Failure'
    }
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        response_object['message'] = 'User not found.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    data = UserSerializer(user).data

    try:
        child = Child.objects.get(id=id)
        data['record'] = RecordSerializer(child.record).data
    except Child.DoesNotExist:
        data['record'] = {}

    response_object['status'] = 'Success'
    response_object['user'] = data
    return JsonResponse(response_object, status=status.HTTP_200_OK)


"""
ORDERS Routes
"""
@api_view(['GET'])
def orders(request):
    # Get products
    sy = SchoolYear.objects.get(is_active=True)
    products = sy.products.all()
    return render(request, 'intern/Order/Orders.html', {
        'products': [x.to_json() for x in products],
    })


@api_view(['GET'])
def order_print(request, pk):
    order = OrderHelper.get_order_by_id(pk)

    # Get payer and caster data
    try:
        user = User.objects.get(pk=order['caster'])
        caster = {
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
    except User.DoesNotExist:
        caster = {'id': order['caster']} 

    try:
        user = User.objects.get(pk=order['payer'])
        payer = {
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
    except User.DoesNotExist:
        payer = {'id': order['payer']}       

    # Update order
    order['caster'] = caster
    order['payer'] = payer


    # Get unique children
    c = []
    for ticket in order['tickets']:
        if ticket['payee'] not in c:
            c.append(ticket['payee'])

    sy = SchoolYear.objects.get(is_active=True)
    intel = SiblingIntels.objects.filter(sibling__parent=user.id, school_year=sy.id)

    # Get children
    children = {}
    for _ in c:
        try:
            user = User.objects.get(pk=_)
            child = {
                'id': _,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }

            record = Record.objects.get(child=user.id, school_year=sy.id)
            if intel:
                child['q1'] = ChildQuotient(intel[0].quotient_1).name
                child['q2'] = ChildQuotient(intel[0].quotient_2).name

            child['school'] = record.school
            child['classroom'] = ChildClass(record.classroom).name

        except User.DoesNotExist:
            child = {'id': _} 
        except Record.DoesNotExist:
            pass
        children[_] = child

    # print (children)

    # Convert tickets to JSON
    order['tickets'] = json.dumps(order['tickets'])

    print (order['tickets'])

    # Get products
    # sy = SchoolYear.objects.get(pk=22)
    sy = SchoolYear.objects.get(is_active=True)
    # print (SchoolYearSerializer(sy).data)
    products = sy.products.all()

    return render(request, 'intern/Order/Print_.html', {
        'order': order,
        'children': children,
        'products': [x.to_json() for x in products],
    })


@api_view(['GET'])
def api_order_get(request, order):
    response_object = {
        'status': 'Failure'
    }
    data = OrderHelper.get_order_by_id(order)

    if not data:
        response_object['message'] = 'Order not found.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    response_object['status'] = 'Success'
    response_object['order'] = data
    return JsonResponse(response_object, status=status.HTTP_200_OK)


@api_view(['GET'])
def api_order_get_details(request, order):
    response_object = {
        'status': 'Failure'
    }
    data = OrderHelper.get_order_by_id(order)

    if not data:
        response_object['message'] = 'Order not found.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    response_object['status'] = 'Success'

    # Get caster
    try:
        _caster = User.objects.get(pk=data['caster'])
        data['caster'] = UserSerializerShort(_caster).data
    except User.DoesNotExist:
        pass

    # Get payer
    try:
        _payer = User.objects.get(pk=data['payer'])
        data['payer'] = UserSerializerShort(_payer).data
    except User.DoesNotExist:
        pass

    response_object['order'] = data
    return JsonResponse(response_object, status=status.HTTP_200_OK)


@api_view(['GET'])
def api_order_date(request, date):
    response_object = {
        'status': 'Failure'
    }

    try:
        orders = Order.objects.filter(date__contains=date, type__gte=1, type__lte=2)
    except Exception as e:
        response_object['message'] = 'An exception occured with error: ' + \
            str(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    if not orders:
        response_object['message'] = 'No order found.'
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    serializer = OrderSerializer(orders, many=True)

    for order in serializer.data:
        try:
            _caster = User.objects.get(pk=order['caster'])
            order['caster'] = UserSerializerShort(_caster).data
        except User.DoesNotExist:
            pass

        # Get payer
        try:
            _payer = User.objects.get(pk=order['payer'])
            order['payer'] = UserSerializerShort(_payer).data
        except User.DoesNotExist:
            pass

    response_object['status'] = 'Success'
    response_object['orders'] = serializer.data
    return JsonResponse(response_object, status=status.HTTP_200_OK)


""" Release 1.5.2 - See order.views """
""" pay/reserve/verify """
"""
@api_view(['POST'])
def api_order_pay(request):
    response_object = {
        'status': 'Failure'
    }
    if not request.data:
        response_object['message'] = 'Empty payload.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    pay_response = OrderHelper.pay(data)
    if pay_response['status'] == 'Failure':
        return JsonResponse(pay_response, status=status.HTTP_400_BAD_REQUEST)
    return JsonResponse(pay_response, status=status.HTTP_200_OK)


@api_view(['POST'])
def api_order_reserve(request):
    response_object = {
        'status': 'Failure'
    }
    if not request.data:
        response_object['message'] = 'Empty payload.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    reserve_response = OrderHelper.reserve(data)
    if reserve_response['status'] == 'Failure':
        return JsonResponse(reserve_response, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse(reserve_response, status=status.HTTP_200_OK)


@api_view(['POST'])
def api_order_verify(request):
    response_object = {
        'status': 'Failure'
    }
    if not request.data:
        response_object['message'] = 'Empty payload.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    verify_response = OrderHelper.verify(data)
    if verify_response['status'] == 'Failure':
        return JsonResponse(verify_response, status=status.HTTP_400_BAD_REQUEST)
        
    return JsonResponse(verify_response, status=status.HTTP_200_OK)
"""
    

"""
USERS Routes
"""

def users_pk(request, pk):
    # Get user without serialization
    user = UsersHelper._user_read(pk)
    if not user:
        return render(request, 'intern/Users_User.html', {'user': {}})

    # Outputs are different by role
    
    # Parent filter
    if user.roles.filter(slug__contains='parent'):
        print ('parent')
        # Get parent sibling
        _sibling = Sibling.objects.filter(parent=user.id).first()

        # Get parent families
        _families = Family.objects.filter(parent=user.id)

        # Store IDs to avoid duplicate in sibling/family
        ids_found = {}

        # Get parent child(ren) 
        family = []
        sibling = []

        try:
            if _sibling:
                # Loop througth children
                for x in _sibling.siblings.all():
                    
                    # Check no duplicate
                    if x.child in ids_found:
                        continue

                    # Register ID
                    ids_found[x.child] = []

                    _child = User.objects.get(id=x.child)
                    __child = UserSerializerShort(_child)

                    sibling.append(__child.data)

            if _families:
                # Loop througth children
                for x in _families.all():

                    # Check no duplicate
                    if x.child in ids_found:
                        continue

                    # Register ID
                    ids_found[x.child] = []

                    _child = User.objects.get(id=x.child)
                    __child = UserSerializerShort(_child)

                    family.append(__child.data)
        except User.DoesNotExist:
            return render(request, 'intern/Users_User.html', {'user': {}})

        return render(request, 'intern/Users_User.html', {'user': user, 'sibling': sibling, 'family': family})
    
    # Child filter
    if user.roles.filter(slug='child'):

        # Get user record
        try:
            _record = Record.objects.get(child=user.id)
        except Record.DoesNotExist:
            print('Record DoesNotExist')
            return render(request, 'intern/Users_User.html', {'user': {}})

        record = RecordSerializer(_record).data

        # Get child tickets 
        # orders = []

        _orders = Order.objects.filter(tickets__payee=user.id)
        # __orders = OrderSerializer(_orders, many=True)
        
        # for order in __orders.data:
        #     for ticket in order.tickets.all():

        return render(request, 'intern/Users_User.html', {'user': user, 'record': record, 'child_orders': _orders})

    return render(request, 'intern/Users_User.html', {'user': user})


def users_add(request):
    pass


"""
MIGRATION/BACKUP Routes
"""
@api_view(['POST'])
def migration_user(request):
    response_object = {
        'status': 'Failure'
    }

    if not request.data:
        response_object['message'] = 'Empty payload.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    result = UsersHelper.post(data)

    if type(result) is str:
        response_object['message'] = result
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    response_object['user'] = result.id
    return JsonResponse(response_object, status=status.HTTP_200_OK)


@api_view(['POST'])
def migration_child(request):
    response_object = {
        'status': 'Failure'
    }

    if not request.data:
        response_object['message'] = 'Empty payload.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    # Create Child
    child = RegistrationHelper.Child.create(data['id'])

    data['is_active'] = True
    data['is_auto_password'] = False
    data['roles'] = ['child']

    result = UsersHelper._users(data)

    if type(result) is str:
        response_object['message'] = result
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    response_object['user'] = result.id
    return JsonResponse(response_object, status=status.HTTP_200_OK)


@api_view(['POST'])
def migration_family(request):
    response_object = {
        'status': 'Failure'
    }

    if not request.data:
        response_object['message'] = 'Empty payload.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    # Get child
    try:
        child = Child.objects.get(pk=data['child'])
    except Child.DoesNotExist:
        child = RegistrationHelper.Child.create(data['child'])

    result = RegistrationHelper.Family.create(child, data['parent'], data['id'])

    if type(result) is str:
        response_object['message'] = result
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    response_object['family'] = result.id
    return JsonResponse(response_object, status=status.HTTP_200_OK)


@api_view(['POST'])
def migration_record(request):
    response_object = {
        'status': 'Failure'
    }

    if not request.data:
        response_object['message'] = 'Empty payload.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    # Get child
    try:
        child = Child.objects.get(pk=data['child_id'])
    except Child.DoesNotExist:
        child = RegistrationHelper.Child.create(data['child_id'])

    result = RegistrationHelper.Record.create(child, data)

    if type(result) is str:
        response_object['message'] = result
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    response_object['record'] = result.id
    return JsonResponse(response_object, status=status.HTTP_200_OK)


@api_view(['POST'])
def migration_sibling(request):
    response_object = {
        'status': 'Failure'
    }

    if not request.data:
        response_object['message'] = 'Empty payload.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)


    result = RegistrationHelper.Sibling.create(data)

    if type(result) is str:
        response_object['message'] = result
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    response_object['record'] = result.id
    return JsonResponse(response_object, status=status.HTTP_200_OK)


@api_view(['POST'])
def migration_order(request):
    response_object = {
        'status': 'Failure'
    }

    if not request.data:
        response_object['message'] = 'Empty payload.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    data = get_parsed_data(request.data)

    result = OrderHelper._create(data)

    if type(result) is str:
        response_object['message'] = result
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    response_object['order'] = result.id
    return JsonResponse(response_object, status=status.HTTP_200_OK)


def migration_orders(request):
    _orders = Order.objects.filter(date__gte='2020-03-01')

    print (len(_orders))

    users = {};
    products = {};
    orders_response = [];

    """ Return last_name and first_name of a given user ID """
    def user_macro(id):
        try:
            user = User.objects.get(id=id)
            return '{} {}'.format(user.last_name, user.first_name)
        except User.DoesNotExist:
            raise Exception('User {} does not exist.'.format(id))
        return False

    """ Return slug of a given product ID """
    def product_macro(id):
        try:
            product = Product.objects.get(id=id)
            return product.slug
        except Product.DoesNotExist:
            raise Exception('Product {} does not exist.'.format(id))
        return False


    for order in _orders:      

        # Get caster/payer informations
        try:
            if order.caster not in users:
                users[order.caster] = user_macro(order.caster)

            if order.payer not in users:
                users[order.payer] = user_macro(order.payer)

        except Exception as e:
            print('Exception raised with error: {}.'.format(str(e)))
            return render(request, 'intern/Backup/Simple_orders_backup.html', {})
        
        # Build order response
        order_response = {
            'id':           order.id,
            'name':         order.name,
            'comment':      order.comment,
            'type':         OrderTypeEnum(order.order_type).name,
            'reference':    order.reference,
            'date':         order.date,
            'caster':       users[order.caster],
            'payer':        users[order.payer],

            'amount_cash':  0.0,
            'amount_check': 0.0,
            'reference_check': '',

            'tickets': []
        }

        # Methods
        for method in order.methods.all():
            # CASH
            if method.method == 1:
                order_response['amount_cash'] += method.amount

            # CHECK
            if method.method == 2:
                order_response['amount_check'] += method.amount
                order_response['reference_check'] = method.reference

        # Tickets
        for ticket in order.tickets.all():
            try:
                # Get payee informations
                if ticket.payee not in users:
                    users[ticket.payee] = user_macro(ticket.payee)

                # Get product slug
                if ticket.product not in products:
                    products[ticket.product] = product_macro(ticket.product)

            except Exception as e:
                print('Exception raised with error: {}.'.format(str(e)))
                return render(request, 'intern/Backup/Simple_orders_backup.html', {})

            # Create ticket response
            order_response['tickets'].append({
                'id': ticket.id,
                'payee': users[ticket.payee],
                'price': ticket.price,
                'product': products[ticket.product]
            })

        # Append order
        orders_response.append(order_response)

    return render(request, 'intern/Backup/Simple_orders_backup.html', {'orders': orders_response})
