import json
import requests

from datetime import datetime

from django.db import transaction
from django.http import QueryDict

from .models import Family, Record, CAF, Health, ChildClass, ChildPAI, ChildQuotient, Sibling, SiblingChild, SiblingIntels
from .forms import IntelForm
from .serializers import RecordSerializer

from users.utils import InternalErrorException, BadRequestException, UnauthorizedException, ForbiddenException, NotFoundException, _localize
from params.models import SchoolYear


class IntelHelper:

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
                raise InternalErrorException('Sibling is not set')

            f = IntelForm(data)
            if not f.is_valid():
                raise BadRequestException('Formulaire incorrect', f.errors)

            # recipent_number is required
            quotient_1 = ChildQuotient.UNSET
            quotient_2 = ChildQuotient.UNSET
            school_year = 0
            recipent_number = f.cleaned_data['recipent_number']
            print (recipent_number)

            print ('1')

            if is_admin:
                quotient_1 = f.cleaned_data.get('quotient_1', ChildQuotient.UNSET)
                quotient_2 = f.cleaned_data.get('quotient_2', ChildQuotient.UNSET)
                school_year = f.cleaned_data.get('school_year', 0)

            print ('2')
            if not school_year:
                _ = SchoolYear.objects.get(is_active=True)
                school_year = _.id

            print ('3')
            intel = sibling.add_intels({
                'quotient_1': quotient_1,
                'quotient_2': quotient_2,
                'recipent_number': recipent_number,
            }, school_year)  
            
            if not intel:
                raise ForbiddenException('L\'objet existe déjà.')  
                # raise BadRequestException('Intel already exist')  

            verified = f.cleaned_data.get('verified', False)
            if intel and is_admin and verified:
                intel.date_verified = _localize(datetime.now())
                intel.save()

            return intel
        
        except SchoolYear.DoesNotExist:
            raise BadRequestException('Année scolaire introuvable.')
        
        except KeyError as e:
            if e.args:
                raise BadRequestException('Erreur d\'index ({}).'.format(str(e.args[0])))
            raise BadRequestException('Erreur d\'index.')

        except Exception as e:
            if e.args:
                raise BadRequestException('Payload invalid ({}).'.format(str(e.args[0])))
            raise BadRequestException('Payload invalid.')

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
                    raise InternalErrorException('Sibling is not set')

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
                        raise ForbiddenException('Inscription fermée à cette période.')

                    # Check own intel
                    if not sibling.intels.filter(pk=pk):
                        raise ForbiddenException('Vous n\'êtes pas autorisé à accéder à cette ressource.')
                        
                    return IntelHelper.update(sibling, data)

                intel = IntelHelper._update_intel(intel, data, is_admin)

            return intel

        except SchoolYear.DoesNotExist:
            raise ForbiddenException('Inscription fermée à cette période.')

        except SchoolYear.MultipleObjectsReturned:
            raise InternalErrorException('Multiple objets année scolaire.')

        except SiblingIntels.DoesNotExist:
            raise NotFoundException('Information introuvable.')

        except SiblingIntels.MultipleObjectsReturned:
            raise InternalErrorException('Multiple objets inscription.')
        
        except (KeyError, Exception) as e:
            if e.args:
                raise BadRequestException('Invalid payload ({})'.format(str(e.args[0])))
            raise BadRequestException('Invalid payload')


    @staticmethod
    def _update_intel(intel, data, is_admin=False):
        f = IntelForm(data)
        if not f.is_valid():
            raise BadRequestException('Formulaire incorrect', f.errors)
        
        def if_not_false(v, k):
            return f.cleaned_data[k] if f.cleaned_data[k] else v 

        intel.recipent_number = f.cleaned_data['recipent_number']
        
        if is_admin:
            intel.quotient_1 = if_not_false(intel.quotient_1, 'quotient_1')
            intel.quotient_2 = if_not_false(intel.quotient_2, 'quotient_2')
            intel.school_year = if_not_false(intel.school_year, 'school_year')
            intel.date_created = if_not_false(intel.date_created, 'date_created')

            intel.date_verified = _localize(datetime.now())

        intel.date_last_mod = _localize(datetime.now())
        intel.save()
        return intel


"""
{
    "parents": [
        {
            "first_name": "...",
            "last_name": "...",
            "emails": [
                {
                    "type": "HOME",
                    "email": "..."
                }
            ],
            "phones": [
                {
                    "type": "HOME",
                    "number": "..."
                }
            ],
            "children": ["id", "id", "..."]
        }
    ],
    "children": [
        {
            "first_name": "...",
            "last_name": "...",
            "dob": "..."
        }
    ],
    "records": [
        {
            "school": "GOND",
            "classroom": "CP",
            "child_id": 78,
            "caf": {
                "q1": "NE",
                "q2": "Q2"
            },
            "health": {
                "asthme": true,
                "allergy_food": true,
                "allergy_grug": true,
                "allergy_food_details": "...",
                "allergy_grug_details": "...",
                "pai": "YES"
            }
        }
    ]
}
"""

"""
    school
    classroom
    date_created
    date_verified   - blank
    date_last_mod   - blank
    child_id
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
@transaction.atomic
def create_record(data):
    sid = transaction.savepoint()
    
    try:

        flag = 'Record object'
        r = Record.objects.create(
            school=data['school'],
            child_id=data['child_id'],
            classroom=data['classroom'],
        )
        r.save()


        """ CAF Handle """
        print(data['caf'])
        flag = 'CAF object'

        c = CAF.objects.create(
            quotient_q1=data['caf']['q1'],
            quotient_q2=data['caf']['q2'],
            recipent_number=data['caf']['recipent_number'],
            record=r
        )
        """ Cmpl verification - pass for speed
        q1 = ChildQuotient.NE
        q2 = ChildQuotient.NE

        if 'q1' in data['caf'] and data['caf']['q1']:
            q1 = data['caf']['q1']

        if 'q2' in data['caf'] and data['caf']['q2']:
            q2 = data['caf']['q2']

        rn = 0
        if 'recipent_number' in data['caf'] and data['caf']['recipent_number']:
            rn = data['caf']['recipent_number']

        c = CAF.objects.create(
            q1 = q1,
            q2 = q2,
            recipent_number = rn,
            record=r
        )
        """
        c.save()

        flag = 'Health object'
        health = data['health']
        print(health)

        h = Health.objects.create(
            pai =                   health['pai'],
            asthme =                health['asthme'],
            allergy_food =          health['allergy_food'],
            allergy_drug =          health['allergy_drug'],
            allergy_food_details =  health['allergy_food_details'],
            allergy_drug_details =  health['allergy_drug_details'],
            record=r,
        )
        h.save()

        print('end')
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


"""
    child_id
    parent_id
"""
@transaction.atomic
def create_family(data):
    sid = transaction.savepoint()
    try:
        family = Family.objects.create(
            child=data['child'],
            parent=data['parent']
        )
        transaction.savepoint_commit(sid)
        return family
    except:
        transaction.savepoint_rollback(sid)
        print ('rollback')
        return 'An exception occured during family creattion.'

    return 'End of function.'



""" MIGRATION """
"""
{
    "parents": [
        {
            "first_name": "...",
            "last_name": "...",
            "emails": [
                {
                    "type": "HOME",
                    "email": "..."
                }
            ],
            "phones": [
                {
                    "type": "HOME",
                    "number": "..."
                }
            ],
            "children": ["id", "id", "..."]
        }
    ],
    "children": [
        {
            "first_name": "...",
            "last_name": "...",
            "dob": "..."
        }
    ],
    "records": [
        {
            "school": "GOND",
            "classroom": "CP",
            "child_id": 78,
            "caf": {
                "q1": "NE",
                "q2": "Q2"
            },
            "health": {
                "asthme": true,
                "allergy_food": true,
                "allergy_grug": true,
                "allergy_food_details": "...",
                "allergy_grug_details": "...",
                "pai": "YES"
            }
        }
    ]
}
"""

"""
    school
    classroom
    date_created
    date_verified   - blank
    date_last_mod   - blank
    child_id
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
@transaction.atomic
def create_record_migration(data):
    sid = transaction.savepoint()

    try:
        # Verify id
        if not 'id' in data:
            return 'No ID provided.'

        flag = 'Record object'
        r = Record.objects.create(
            id=data['id'],
            school=data['school'],
            child_id=data['child_id'],
            classroom=data['classroom'],
        )
        r.save()

        """ CAF Handle """
        # print(data['caf'])
        flag = 'CAF object'

        c = CAF.objects.create(
            quotient_q1=data['caf']['q1'],
            quotient_q2=data['caf']['q2'],
            recipent_number=data['caf']['recipent_number'],
            record=r
        )

        """ Cmpl verification - pass for speed
        q1 = ChildQuotient.NE
        q2 = ChildQuotient.NE

        if 'q1' in data['caf'] and data['caf']['q1']:
            q1 = data['caf']['q1']

        if 'q2' in data['caf'] and data['caf']['q2']:
            q2 = data['caf']['q2']

        rn = 0
        if 'recipent_number' in data['caf'] and data['caf']['recipent_number']:
            rn = data['caf']['recipent_number']

        c = CAF.objects.create(
            q1 = q1,
            q2 = q2,
            recipent_number = rn,
            record=r
        )
        """
        c.save()

        flag = 'Health object'
        health = data['health']
        # print(health)

        h = Health.objects.create(
            pai=health['pai'],
            asthme=health['asthme'],
            allergy_food=health['allergy_food'],
            allergy_drug=health['allergy_drug'],
            allergy_food_details=health['allergy_food_details'],
            allergy_drug_details=health['allergy_drug_details'],
            record=r,
        )
        h.save()

        print('end')
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


"""
    child_id
    parent_id
"""
@transaction.atomic
def create_family_migration(data):
    sid = transaction.savepoint()
    try:
        # Verify id
        if not 'id' in data:
            return 'No ID provided.'
            
        family = Family.objects.create(
            id=data['id'],
            child=data['child'],
            parent=data['parent']
        )
        transaction.savepoint_commit(sid)
        return family
    except:
        transaction.savepoint_rollback(sid)
        print('rollback')
        return 'An exception occured during family creation.'

    return 'End of function.'


"""
id
parent
children [child_id]
"""
@transaction.atomic
def create_siblings_migration(data):
    sid = transaction.savepoint()
    try:
        # Verify id
        if not 'id' in data:
            return 'No ID provided.'

        sibling = Sibling.objects.create(
            id=data['id'],
            parent=data['parent'],
        )

        for child in data['children']:
            sibling.siblings.create(
                child=child
            )

        transaction.savepoint_commit(sid)
        return sibling
    except:
        transaction.savepoint_rollback(sid)
        print('rollback')
        return 'An exception occured during sibling creation.'

    return 'End of function.'
