from django import forms
from django.core.exceptions import ValidationError

from .models import HistoryTypeEnum as HTE

def clean_type(data):
    try:
        HTE(data)
        return data
    except:
        raise ValidationError('Type invalide, doit être compris entre 1 et 7.')

class ClientForm(forms.Form):
    type = forms.IntegerField() # HistoryTypeEnum
    credit = forms.FloatField()
    comment = forms.CharField(widget=forms.Textarea, required=False)

    def clean_type(self):
        return clean_type (self.cleaned_data['type'])

class HistoryForm(forms.Form):
    type = forms.IntegerField()
    caster = forms.IntegerField()
    comment = forms.CharField(widget=forms.Textarea, required=False)

    def clean_type(self):
        return clean_type (self.cleaned_data['type'])