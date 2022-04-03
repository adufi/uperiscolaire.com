from .utils import check_authorizations

def login_required (roles):

    def inner (func):

        def wrapper(request, *args, **kwargs):
            check = check_authorizations(request.headers, roles)
            
            request.META['check'] = check

            resp = func (request, *args, **kwargs)

            return resp

        return wrapper

    return inner