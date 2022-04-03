from django.http import JsonResponse
from rest_framework import status

from .utils import check_authorizations, UnauthorizedException, ForbiddenException

def login_required (roles):

    def inner (func):

        def wrapper(request, *args, **kwargs):
            try:
                check = check_authorizations(request.headers, roles)
            except UnauthorizedException as e:
                return JsonResponse({'message': e.args[0]}, status=status.HTTP_401_UNAUTHORIZED)
            except ForbiddenException as e:
                return JsonResponse({'message': e.args[0]}, status=status.HTTP_403_FORBIDDEN)
            
            request.META['check'] = check

            resp = func (request, *args, **kwargs)

            return resp

        return wrapper

    return inner


""" Login wrapper for View/APIView based class """
def login_required_view (roles):

    def inner (func):

        def wrapper(self, request, *args, **kwargs):
            try:
                check = check_authorizations(self.request.headers, roles)
            except UnauthorizedException as e:
                return JsonResponse({'message': e.args[0]}, status=status.HTTP_401_UNAUTHORIZED)
            except ForbiddenException as e:
                return JsonResponse({'message': e.args[0]}, status=status.HTTP_403_FORBIDDEN)
            
            self.request.META['check'] = check

            resp = func (self, request, *args, **kwargs)

            return resp

        return wrapper

    return inner