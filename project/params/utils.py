import json
import requests

from django.db import transaction
from django.http import QueryDict
from datetime import datetime

from .models import SchoolYear, Product


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


"""
check_authorizations(request, []) => basic auth
check_authorizations(request, ['admin', 'is_superuser'])
"""
def check_authorizations(headers, roles):
    if 'Authorization' in headers:
        try:
            token = headers.get('Authorization').split(' ')[1]
            r = requests.get('http://localhost:8000/ap/auth/status/', headers={'Authorization': f'Bearer {token}'})
            if r.status_code != 200:
                return 'Failed to get status'

            user = r.json()['user']

            if not roles:
                return True

            if not hasattr(user, 'roles') and not user['roles']:
                return 'User has not roles'

            for role in user['roles']:
                print (role['slug'])
                if role['slug'] in roles:
                    return True

            return 'Function ended'
        except IndexError:
            return 'Function threw IndexError'
    else:
        return 'Headers doesn\t have bearer'


"""
{
    school_year {
        date_start
        date_end
    }
    days_off [{
        date
    }]
    peri_months [{
        slug
        title
        order
    }]
    alsh_vacations [{
        slug
        title
        date_start
        date_end
        days [{
            slug
            title
            date
            category
        }]
    }]
}

NOTES
    - Can't create two SY with the same dates
"""
@transaction.atomic
def create_schoolyear(data):
    sid = transaction.savepoint()
    try:
        _date_start = data['school_year']['date_start']
        _date_end = data['school_year']['date_end']

        date_start = datetime.strptime(_date_start, '%Y-%m-%d')
        date_end = datetime.strptime(_date_end, '%Y-%m-%d')

        ss = SchoolYear.objects.filter(date_start__contains=str(date_start.year))

        if ss:
            return 'SchoolYear with year already exist'

        s = SchoolYear.objects.create(
            date_start=date_start,
            date_end=date_end,
        )

        # Add Days Off
        for day_off in data['days_off']:
            s.daysoff.add(DaysOff(
                date=day_off['date'],
            ))

        # Add Months
        for month in data['peri_months']:
            s.perimonth.add(PeriMonth(
                slug=month['slug'],
                title=month['title'],
                order=month['order']
            ))

        # Add Vacations/Vacation days
        for vac in data['alsh_vacations']:
            ds = datetime.strptime(vac['date_start'], '%Y-%m-%d')
            de = datetime.strptime(vac['date_end'], '%Y-%m-%d')

            v = AlshVacation.objects.create(
                slug=vac['slug'],
                title=vac['title'],
                date_start=ds,
                date_end=de,
                school_year=s
            )

            for day in vac['days']:
                d = datetime.strptime(day['date'], '%y-%m-%d')
                v.alshvacationday.add(AlshVacationDay(
                    slug=day['slug'],
                    title=day['title'],
                    date=d,
                    category=day['category'],
                ))
                
        transaction.savepoint_commit(sid)
        return s

    except Exception as e:
        transaction.savepoint_rollback(sid)
        print ('rollback')
        if e.args:
            return e.args[0]
        return 'An exception occured'
