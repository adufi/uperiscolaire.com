from django import forms
from django.core.exceptions import ValidationError

from .models import Product, CategoryEnum, SubCategoryEnum


class ProductForm (forms.ModelForm):

    # name        = forms.CharField(max_length=128)
    # slug        = forms.CharField(max_length=128)
    # description = forms.CharField(max_length=128)

    # date        = forms.DateField()
    # date_start  = forms.DateField()
    # date_end    = forms.DateField()

    # category        = forms.IntegerField()
    # subcategory     = forms.IntegerField()

    # stock_max       = forms.IntegerField()
    # stock_current   = forms.IntegerField()

    # price       = forms.FloatField()
    # price_q1    = forms.FloatField()
    # price_q2    = forms.FloatField()

    # active = forms.BooleanField()

    # order = models.IntegerField(default=0)

    class Meta:
        model = Product
        fields = [
            'name',
            'slug',
            'description',
            'date',
            'date_start',
            'date_end',
            'category',
            'subcategory',
            'stock_max',
            'stock_current',
            'price',
            'price_q1',
            'price_q2',
            'active',
            'order',
            'school_year'
        ]

    def clean_category (self):
        data = self.cleaned_data['category']

        # if data == 0:
        #     raise ValidationError('Valeur nulle.')

        try:
            CategoryEnum(data)
        except:
            raise ValidationError('Valeur inconnue.')

        return data

    def clean_subcategory (self):
        data = self.cleaned_data['subcategory']

        # if data == 0:
        #     raise ValidationError('Valeur nulle.')

        try:
            SubCategoryEnum(data)
        except:
            raise ValidationError('Valeur inconnue.')

        return data