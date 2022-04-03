from enum import IntEnum
from django.db import models
from django.utils.timezone import now

from params.models import SchoolYear

# Create your models here.
class ReservationType(IntEnum):
    RESERVED = 1
    PAID = 2

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class Product(models.Model):
    name = models.CharField(max_length=200, default='')
    desc = models.CharField(max_length=200, default='')
    slug = models.CharField(max_length=200, default='')

    price = models.IntegerField(default=0)

    stock = models.IntegerField(default=0)
    # stock_cur = models.IntegerField(default=0)
    # stock_max = models.IntegerField(default=0)

    category = models.CharField(max_length=200, default='')
    subcategory = models.CharField(max_length=200, default='')

    school_year = models.IntegerField(default=0)

    def __str__(self):
        return '#{} - {} - {}'.format(self.id, self.name, self.desc)

    def has_stock(self):
        if self.stock_max == 0:
            return True
        if self.stock_cur > 0:
            return True
        return False

    def buy_product(self):
        self.stock_cur -= 1

    def refill_stock(self):
        self.stock_cur = self.stock_max


class ProductReservation(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reservations'
    )

    user = models.IntegerField(default=0)
    date = models.DateTimeField(default=now)
