from django import forms
from django.core.exceptions import ValidationError

from .models import OrderTypeEnum, MethodEnum

class OrderForm(forms.Form):
    name = forms.CharField(max_length=128, required=False)
    comment = forms.CharField(required=False)
    reference = forms.CharField(max_length=128, required=False)

    type = forms.IntegerField()

    caster = forms.IntegerField()
    payer = forms.IntegerField()

    # amount = forms.FloatField()

    def clean_type(self):
        data = self.cleaned_data['type']
        if data == OrderTypeEnum.UNSET:
            raise ValidationError('Type invalide, choix interdit.')
        try:
            _ = OrderTypeEnum(data)
        except ValueError:
            raise ValidationError('Type invalide, valeur inconnue.')
        return data


class OrderMethodForm(forms.Form):
    amount = forms.FloatField()
    method = forms.IntegerField()
    reference = forms.CharField(max_length=128, required=False)

    def clean_method(self):
        data = self.cleaned_data['method']
        if data == MethodEnum.UNSET:
            raise ValidationError('Methode invalide, choix interdit.')
        try:
            _ = MethodEnum(data)
        except ValueError:
            raise ValidationError('Methode invalide, valeur inconnue.')
        return data