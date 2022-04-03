from .forms import ClientForm
from .models import Client
from .serializers import CompleteClientSerializers


""" Actually set_client """
def set_credit(pk, data):
    """
    Parameters
    ----------
    data => dict {
        type        - See ClientCreditHistory
        credit
        caster
        comment
    }

    """
    try:
        client = Client.objects.get(id=pk)
    except Client.DoesNotExist:
        client = Client.objects.create_client(pk)
    
    # Main data
    f = ClientForm(data)
    if f.is_valid():
        client.set_credit(
            data['credit'],
            data['caster'],
            data['type'],
            data['comment']
        )

        return {
            'status': 'Success',
            'client': CompleteClientSerializers(client).data
        }

    else:
        return {
            'status': 'Failure',
            'errors': f.errors,
            'message': 'Formulaire incorrect.'
        }
    # if client.credit != data['credit']:

    # else:

def update_credit(pk, data):
    """
    Parameters
    ----------
    data => dict {
        type        - See ClientCreditHistory
        credit
        caster
        comment
    }

    """
    try:
        client = Client.objects.get(id=pk)
    except Client.DoesNotExist:
        client = Client.objects.create_client(pk)
    
    # Main data
    f = ClientForm(data)
    if f.is_valid():
        client.update_credit(
            data['credit'],
            data['caster'],
            data['type'],
            data['comment']
        )

        return {
            'status': 'Success',
            'client': CompleteClientSerializers(client).data
        }

    else:
        return {
            'status': 'Failure',
            'errors': f.errors,
            'message': 'Formulaire incorrect.'
        }
    # if client.credit != data['credit']:

    # else:
    #     return {'status': 'Failure', 'message': 'Aucun changement effectué.'}