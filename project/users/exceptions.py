import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from rest_framework import status

# 400
class BadRequestException(Exception):
    pass

class FormValidationException(Exception):
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


def handle_exeptions(e, default='Une erreur est survenue.'):
    if e.args:
        return e.args[0]
    else:
        return default


def exception_to_response (e, extra=None):
    response_object = {'status': 'Failure'}
    if extra:
        response_object.update(extra)

    # 400 Errors
    if isinstance(e, KeyError):
        # response_object['message'] = f'Une erreur est survenue ({str(e)}).'
        response_object['message'] = f'Erreur clé {str(e)}.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(e, BadRequestException):
        # response_object['message'] = f'Une erreur est survenue ({str(e)}).'
        response_object['message'] = handle_exeptions(e)
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(e, FormValidationException):
        response_object['errors'] = e.args[0]
        response_object['message'] = 'Formulaire incorrect.'
        return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

    # 403 Forbidden
    if isinstance(e, ForbiddenException):
        response_object['message'] = handle_exeptions(e, 'Vous n\'êtes pas autorisé à consulter cette ressource.')
        return JsonResponse(response_object, status=status.HTTP_403_FORBIDDEN)

    # 404 Errors
    if isinstance(e, ObjectDoesNotExist) or isinstance(e, NotFoundException):
        response_object['message'] = handle_exeptions(e, f'Objet introuvable.')
        return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    print (str(e))
    response_object['message'] = str(e)
    return JsonResponse(response_object, status=status.HTTP_500_INTERNAL_SERVER_ERROR)