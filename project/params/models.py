from enum import IntEnum
from django.db import models
from django.utils.timezone import now

# Create your models here.


class CategoryEnum(IntEnum):
    UNSET                   = 0
    PERI                    = 1
    JANVIER                 = 2
    FEVRIER                 = 3
    MARS                    = 4
    AVRIL                   = 5
    MAI                     = 6
    JUIN                    = 7
    JUILLET                 = 8
    AOUT                    = 9
    SEPTEMBRE               = 10
    OCTOBRE                 = 11
    NOVEMBRE                = 12
    DECEMBRE                = 13
    TOUSSAINT               = 14
    NOEL                    = 15
    CARNAVAL                = 16
    PAQUES                  = 17
    GRDS_VACANCES_JUILLET   = 18
    GRDS_VACANCES_AOUT      = 19

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class SubCategoryEnum(IntEnum):
    UNSET   = 0
    MINUS6  = 1
    PLUS6   = 2

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class SchoolYear(models.Model):
    date_start = models.DateField(null=False)
    date_end = models.DateField(null=False)

    is_active = models.BooleanField(default=False)

    # Flag to order school years
    # order = models.IntegerField(default=0)

    class Meta:
        ordering = ['-date_start']

    def _is_active(self):
        tnow = now().replace(tzinfo=None)
        return (tnow.date() > self.date_start and tnow.date() < self.date_end)

    def to_json(self):
        return {
            'id': self.id,
            # 'order': self.order,
            'is_active': self.is_active,

            'date_start': self.date_start.__str__(),
            'date_end': self.date_end.__str__(),
        }

    def __str__(self):
        return '#{} - {}-{} '.format(self.id, self.date_start.year, self.date_end.year) + ('(active)' if self.is_active else '')


class Product(models.Model):
    name = models.CharField(max_length=128, default='')
    slug = models.CharField(max_length=128, default='')
    description = models.CharField(max_length=128, default='', blank=True)

    order = models.IntegerField(default=0)
    date = models.DateField(null=True, blank=True)

    category = models.IntegerField(choices=CategoryEnum.choices(), default=CategoryEnum.UNSET)
    subcategory = models.IntegerField(choices=SubCategoryEnum.choices(), default=SubCategoryEnum.UNSET)

    # stock = models.IntegerField(default=0)
    stock_max = models.IntegerField(default=0)
    stock_current = models.IntegerField(default=0)

    price = models.FloatField(default=0.0)
    price_q1 = models.FloatField(default=0.0)
    price_q2 = models.FloatField(default=0.0)

    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)

    active = models.BooleanField(default=True)

    school_year = models.ForeignKey(
        SchoolYear,
        on_delete=models.CASCADE,
        related_name='products'
    )

    class Meta:
        ordering = ['school_year', 'order', 'subcategory', 'date']

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,

            'date':     self.date,
            'order':    self.order,

            'category': self.category,
            'subcategory': self.subcategory,

            'stock_max': self.stock_max,
            'stock_current': self.stock_current,

            'price': self.price,
            'price_q1': self.price_q1,
            'price_q2': self.price_q2,

            'date_start':   self.date_start,
            'date_end': self.date_end,

            'active': self.active,
        }

    def __str__(self):
        return '#{} - {} - {}'.format(self.id, self.name, self.school_year)


class ProductStock(models.Model):
    count = models.IntegerField(default=0)
    max = models.IntegerField(default=0)

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='stock'
    )

    # def __init__(self, max, product, count=0):
    #     self.count = count
    #     self.product = product
    #     self.max = max

    def __str__(self):
        return '#'


# class AlshReservation(models.Model):
#     day = models.ForeignKey(
#         AlshVacationDay,
#         on_delete=models.CASCADE,
#         related_name='reservations'
#     )

#     user = models.IntegerField(default=0)
#     date = models.DateTimeField(default=now)


"""
class CategoryEnum(IntEnum):
    UNSET                   = 0
    PERI                    = 1
    SEPTEMBRE               = 2
    OCTOBRE                 = 3
    NOVEMBRE                = 4
    DECEMBRE                = 5
    TOUSSAINT               = 6
    NOEL                    = 7
    JANVIER                 = 8
    FEVRIER                 = 9
    MARS                    = 10
    CARNAVAL                = 11
    AVRIL                   = 12
    MAI                     = 13
    JUIN                    = 14
    JUILLET                 = 15
    PAQUES                  = 16
    AOUT                    = 17
    GRDS_VACANCES_JUILLET   = 18
    GRDS_VACANCES_AOUT      = 19

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]
"""
