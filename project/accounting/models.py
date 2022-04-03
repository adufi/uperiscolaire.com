from enum import IntEnum
from django.db import models
from django.utils.timezone import now

from datetime import datetime


# Enums

class HistoryTypeEnum(IntEnum):
    UNSET   = 0
    USER_ENTERED = 1
    ORDER_CANCELATION = 2
    TICKET_CANCELATION = 3
    CREDIT_CONSUMED = 4
    REFUND = 5
    SYSTEM_OP = 6
    MIGRATION = 7

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


# Create your models here.

class ClientManager(models.Manager):
    def create_client(self, id):
        client = self.create(id=id)
        client.save()
        return client


class Client(models.Model):
    id = models.IntegerField(primary_key=True)
    credit = models.FloatField(default=0.0)
    date_created = models.DateTimeField(default=now)

    objects = ClientManager()

    class Meta:
        ordering = ['id']

    @classmethod
    def create(cls, id):
        client = cls(id=id)
        client.save()
        return client

    """ Credit modification """
    def set_credit(self, credit, caster, type, comment=''):
        self.credit_macro(credit, caster, type, comment)

    def update_credit(self, credit, caster, type, comment=''):
        new_credit = self.credit + credit
        self.credit_macro(new_credit, caster, type, comment)

    def credit_macro(self, credit, caster, type, comment=''):
        # create history
        self.credit_history.create(
            value=self.credit,
            caster=caster,
            comment=comment,
            type=type,
        )

        # Save own data
        self.credit = credit
        self.save()

    def __str__(self):
        return '#{}'.format(self.id)


class ClientCreditHistory(models.Model):
    date = models.DateTimeField(default=now)

    value = models.IntegerField()
    caster = models.IntegerField()

    comment = models.TextField(default='') # Should be required

    type = models.IntegerField(choices=HistoryTypeEnum.choices(), default=HistoryTypeEnum.UNSET)

    credit = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='credit_history'
    )

    class Meta:
        ordering = ['-date']

    def update (self, type, caster, comment):
        self.type = type
        self.caster = caster
        self.comment = comment
        self.save()

    def __str__(self):
        return '#{} - Client #{} - Amount ({}) - Date ({})'.format(self.id, self.credit.id, self.value, self.date)


# class ClientCredit(models.Model):
#     amount = models.FloatField(default=0.0)

#     client = models.OneToOneField(
#         Client,
#         on_delete=models.CASCADE,
#         related_name='credit'
#     )

#     def set(self, amount, caster, type, comment=''):
#         self._macro(amount, caster, type, comment)

#     def update(self, amount, caster, type, comment=''):
#         new_amount = self.amount + amount
#         self._macro(new_amount, caster, type, comment)

#     def _macro(self, amount, caster, type, comment=''):
#         # create history
#         self.history.create(
#             value=self.amount,
#             caster=caster,
#             comment=comment,
#             type=type,
#         )

#         # Save own data
#         self.amount = amount
#         self.save()

#     def __str__(self):
#         return '#{} -  for Client: {}'.format(self.id, self.client)