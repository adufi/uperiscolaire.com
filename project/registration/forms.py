from django import forms
from django.core.exceptions import ValidationError

from .models import ChildQuotient


class IntelForm(forms.Form):
    recipent_number = forms.IntegerField()

    quotient_1 = forms.IntegerField(required=False)
    quotient_2 = forms.IntegerField(required=False)

    school_year = forms.IntegerField(required=False)

    date_created = forms.DateTimeField(required=False)
    date_last_mod = forms.DateTimeField(required=False)
    date_verified = forms.DateTimeField(required=False)

    def clean_quotient_1(self):
        data = self.cleaned_data['quotient_1']

        if data == 0:
            self.cleaned_data['quotient_1'] = 1

        elif data < 0 or data > 3:
            raise ValidationError('Type invalide, doit être compris entre 1 et 3.')

        return data

    def clean_quotient_2(self):
        data = self.cleaned_data['quotient_2']

        if data == 0:
            self.cleaned_data['quotient_2'] = 1

        elif data < 0 or data > 3:
            raise ValidationError('Type invalide, doit être compris entre 1 et 3.')

        return data

