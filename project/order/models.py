import pytz

from enum import IntEnum
from django.db import models
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.timezone import now

from datetime import datetime, timedelta

from users.utils import _localize
from users.models import User


""" Utils """
def _localize(date):
    if type(date) is str:
        _ = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    else:
        _ = date
    return pytz.utc.localize(_)

""" Enums """
class OrderTypeEnum(IntEnum):
    UNSET   = 0
    OFFICE  = 1
    DIR     = 2
    ONLINE  = 3
    MIGRATION = 4
    MIGRATION_DIR = 5
    MANUAL = 6

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StatusEnum(IntEnum):
    UNSET       = 0
    RESERVED    = 1
    COMPLETED   = 2
    REPORTED    = 3     # discarded
    REFUNDED    = 4
    CANCELED    = 5
    WAITING     = 6
    CREDITED    = 7

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class MethodEnum(IntEnum):
    UNSET   = 0
    CASH    = 1
    CHECK   = 2
    ONLINE  = 3
    VRMT    = 4
    CREDIT  = 5
    PAYPAL  = 6
    STRIPE  = 7
    ONLINE_VADS = 8

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


""" Models """
class Client(models.Model):
    id = models.IntegerField(primary_key=True)
    user = models.IntegerField()

    def __str__(self):
        return '#{}'.format(self.id)


class ClientCredit(models.Model):
    amount = models.FloatField(default=0.0)
    date_created = models.DateTimeField(default=now)
    date_last_mod = models.DateTimeField(default=now)

    client = models.OneToOneField(
        Client,
        on_delete=models.CASCADE,
        related_name='credit'
    )

    def set(self, amount):
        self.amount = amount
        self.date_last_mod = _localize(datetime.now())
        self.save()

    def update(self, amount):
        self.amount += amount
        self.date_last_mod = _localize(datetime.now())
        self.save()

    def __str__(self):
        return '#{} - Last mod.: {} for Client: {}'.format(self.id, self.date_last_mod, self.client)


class ClientRefund(models.Model):
    pass


class OrderManager (models.Manager):

    def orders_waiting (self, payer):
        if not settings.ORDER_WAITING_EXPIRATION_DAYS:
            raise ImproperlyConfigured('ORDER_WAITING_EXPIRATION_DAYS n\'est pas configuré')

        date_expired = datetime.now() - timedelta(days=settings.ORDER_WAITING_EXPIRATION_DAYS)

        return self.annotate(status_count=models.Count('status')).filter(status_count=1, status__status=StatusEnum.WAITING, date__gte=_localize(date_expired), payer=payer)

    def expired_orders (self):
        if not settings.ORDER_WAITING_EXPIRATION_DAYS:
            raise ImproperlyConfigured('ORDER_WAITING_EXPIRATION_DAYS n\'est pas configuré')

        date_expired = datetime.now() - timedelta(days=settings.ORDER_WAITING_EXPIRATION_DAYS)

        return self.annotate(status_count=models.Count('status')).filter(status_count=1, status__status=StatusEnum.WAITING, date__lte=_localize(date_expired))

    def expired_orders_by_payer (self, payer):
        if not settings.ORDER_WAITING_EXPIRATION_DAYS:
            raise ImproperlyConfigured('ORDER_WAITING_EXPIRATION_DAYS n\'est pas configuré')

        date_expired = datetime.now() - timedelta(days=settings.ORDER_WAITING_EXPIRATION_DAYS)

        return self.annotate(status_count=models.Count('status')).filter(status_count=1, status__status=StatusEnum.WAITING, date__lte=_localize(date_expired), payer=payer)


""" Order """
class Order(models.Model):
    name = models.CharField(max_length=128, default='Paiement UPEEM')
    comment = models.TextField(default='')

    type = models.IntegerField(choices=OrderTypeEnum.choices(), default=OrderTypeEnum.UNSET)

    # Migration ticket ID
    reference = models.CharField(max_length=128, default='')

    date = models.DateTimeField(default=now)

    # TODO
    # caster id
    # caster name - api forbid query for non admin
    caster = models.IntegerField(default=0)
    payer = models.IntegerField(default=0)

    amount = models.FloatField(default=0.0)
    amount_rcvd = models.FloatField(default=0.0)
    amount_refunded = models.FloatField(default=0.0, blank=True)

    objects = OrderManager()

    def _add_status(self, status):
        # try:
        #     id = OrderStatus.objects.latest('id').id + 1
        # except:
        #     id = 1
        self.status.add(OrderStatus.objects.create(
            # id=id,
            order=self,
            status=status
        ))

    def has_expired (self):
        if not settings.ORDER_WAITING_EXPIRATION_DAYS:
            raise ImproperlyConfigured('ORDER_WAITING_EXPIRATION_DAYS n\'est pas configuré')

        status = self.status.first()
        if status.status == StatusEnum.WAITING:
            if self.date + timedelta(days=settings.ORDER_WAITING_EXPIRATION_DAYS) < _localize(datetime.now()):
                return True

        return False

    """ 
    See utils.cancel_expired_orders
    Not used anymore cause of credit and stocks
    """
    @staticmethod
    def cancel_expired_orders ():
        if not settings.ORDER_WAITING_EXPIRATION_DAYS:
            raise ImproperlyConfigured('ORDER_WAITING_EXPIRATION_DAYS n\'est pas configuré')

        date_expired = datetime.now() - timedelta(days=settings.ORDER_WAITING_EXPIRATION_DAYS)

        orders = Order.objects.annotate(status_count=models.Count('status')).filter(status_count=1, status__status=StatusEnum.WAITING, date__lte=_localize(date_expired))
        for order in orders:
            order.cancel()

    def complete (self):
        if self.status.first().status == StatusEnum.COMPLETED:
            return True

        amount_rcvd = 0
        for method in self.methods.all():
            amount_rcvd += method.amount

        if self.amount > amount_rcvd:
            raise Exception(f'Montant trop faible, attendu ({self.amount - amount_rcvd})') 
        
        elif self.amount < amount_rcvd:
            raise Exception(f'Montant trop élevé, trop perçu ({amount_rcvd - self.amount})') 

        else:
            self._add_status(StatusEnum.COMPLETED)
            for ticket in self.tickets.all():
                ticket._add_status(StatusEnum.COMPLETED)
            return True

        return False

    # Cancel an order if INCOMPLETE and amount is 0
    # Cancel an order if COMPLETE and add credit
    def cancel (self, amount=0):
        status = self.status.first()
        if status and status.status == StatusEnum.COMPLETED:
            self.amount_refunded += amount
            if self.amount_refunded > self.amount:
                return False

            elif self.amount_refunded == self.amount:
                self._add_status(StatusEnum.CANCELED)
                
            self.save()
            return True

        else:
            if not amount:
                self._add_status(StatusEnum.CANCELED)
                return True        
            else:
                return False

    # waiting - to implement for later
    def refund (self, amount):
        status = self.status.first()
        if status and status.status == StatusEnum.COMPLETED:
            self.amount_refunded += amount
            
            if self.amount_refunded > self.amount:
                return False

            elif amount == self.amount:
                self._add_status(StatusEnum.REFUNDED)
                
            self.save()
            return True

        else:
            return False


    class Meta:
        ordering = ['date']

    def __str__(self):
        return f'#{self.id} - {self.name} with ID: {self.payer} and amount: {self.amount}'


class OrderStatus(models.Model):
    date = models.DateTimeField(default=now)
    status = models.IntegerField(
        choices=StatusEnum.choices(), default=StatusEnum.UNSET)

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status'
    )

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'#{self.id} - Date: {self.date} - Status: {StatusEnum(self.status).name}'


class OrderMethod(models.Model):
    method = models.IntegerField(choices=MethodEnum.choices(), default=MethodEnum.UNSET)
    reference = models.CharField(max_length=128, default='')
    amount = models.FloatField(default=0.0)

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='methods'
    )

    def __str__(self):
        return f'{MethodEnum(self.method).name} with reference: {self.reference}'


""" Ticket """
class Ticket(models.Model):
    payee = models.IntegerField(default=0)
    product = models.IntegerField(default=0)

    price = models.FloatField(default=0.0)

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='tickets'
    )

    def report(self):
        self._add_status(StatusEnum.REPORTED)

    def _add_status(self, status):
        # try:
        #     id = TicketStatus.objects.latest('id').id + 1
        # except:
        #     id = 1
        self.status.add(TicketStatus.objects.create(
            # id=id,
            ticket=self,
            status=status
        ))

    def __str__(self):
        return f'#{self.id} - Order ID: {self.order.id} - Payee: {self.payee} - Product: {self.product} - Price: {self.price}'
        # return f'{self.order.name} with ID: {self.payee} and price: {self.price}'


class TicketStatus(models.Model):
    date = models.DateTimeField(default=now)
    status = models.IntegerField(choices=StatusEnum.choices(), default=StatusEnum.UNSET)

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='status'
    )

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f'#{self.id} - Date: {self.date} - Status: {StatusEnum(self.status).name}'


""" Anomalies """
# class Anomaly(models.Model):
#     date = models.DateTimeField(default=now)
    
#     TYPE_CHOICES = (
#         ('amount', 'Amount'),
#         ('completed', 'Completed'),
#     )
#     type = models.CharField(max_length=30, choices=TYPE_CHOICES)

#     order = models.ForeignKey(
#         Order,
#         on_delete=models.CASCADE,
#         related_name='anomalies'
#     )

#     def __str__(self):
#         return f'Order ({self.order.id}) - Type ({self.type})'