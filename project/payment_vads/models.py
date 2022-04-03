import enum

from django.db import models
from django.utils.timezone import now

from users.exceptions import InternalErrorException

# Create your models here.

class OrderStatusEnum (enum.IntEnum):
    WAITING             = 0
    INCORRECT_PAYLOAD   = 10
    INCORRECT_AMOUNT    = 11
    INCORRECT_PRODUCT   = 12
    COMPLETED           = 20
    
    @classmethod
    def choices (cls):
        return [(key.value, key.name) for key in cls]

class TransactionVADSManager(models.Manager):
    def create_transaction (self, data):
        t = TransactionVADS()
        t.amount        = int(data['vads_amount'])
        
        t.trans_id      = data['vads_trans_id']
        t.trans_date    = data['vads_trans_date']
        t.trans_status  = data['vads_trans_status']

        t.cust_email    = data['vads_cust_email']

        if 'vads_ext_info_Informations' in data:
            t.ext_info_1 = data['vads_ext_info_Informations']
        else:
            raise InternalErrorException('Echec de la récupération des informations.')
        
        # if 'vads_ext_info_Paramètres' in data:
        #     t.ext_info_1    = data['vads_ext_info_Paramètres']
        # elif 'vads_ext_info_ParamÃ¨tres' in data:
        #     t.ext_info_1 = data['vads_ext_info_ParamÃ¨tres']
        # elif 'vads_ext_info_Informations' in data:
        #     t.ext_info_1 = data['vads_ext_info_Informations']
        # else:
        #     raise InternalErrorException('Echec de la récupération des informations.')

        t.save()
        return t


class TransactionVADS (models.Model):

    amount = models.IntegerField()
    trans_id = models.CharField(max_length=20)
    trans_date = models.CharField(max_length=20, default= '')
    trans_status = models.CharField(max_length=50)

    cust_email = models.EmailField()

    ext_info_1 = models.TextField()

    order_id = models.PositiveIntegerField(default=0)
    order_status = models.IntegerField(choices=OrderStatusEnum.choices(), default=OrderStatusEnum.WAITING)
    order_message = models.TextField(default='')

    date = models.DateTimeField(default=now)

    objects = TransactionVADSManager()

    def __str__ (self):
        return ''