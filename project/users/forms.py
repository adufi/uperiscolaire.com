from django import forms
from django.core.exceptions import ValidationError

from .models import User, CITIES

class ChildForm(forms.Form):
    # parent_id = forms.IntegerField()

    dob = forms.DateField()
    gender = forms.IntegerField()
    
    last_name = forms.CharField(max_length=128)
    first_name = forms.CharField(max_length=128)

    birthplace = forms.CharField(max_length=128, required=False)

    def clean_gender(self):
        data = self.cleaned_data['gender']

        if data < 1 or data > 2:
            raise ValidationError('Genre invalide, doit être compris entre 1 et 2.')

        return data


class UserForm(forms.Form):
    id = forms.IntegerField(required=False)

    last_name = forms.CharField(max_length=128)
    first_name = forms.CharField(max_length=128)

    gender = forms.IntegerField()

    dob = forms.DateField(required=False)
    job = forms.CharField(max_length=128, required=False)
    birthplace = forms.CharField(max_length=128, required=False)

    accept_newsletter = forms.BooleanField(required=False)

    # Email can't change the regular way
    # email = forms.EmailField(required=False)

    """ Phones """
    phone_cell = forms.CharField(min_length=9, max_length=10)
    phone_home = forms.CharField(min_length=9, max_length=10, required=False)
    phone_pro = forms.CharField(min_length=9, max_length=10, required=False)

    """ Address """
    address_1 = forms.CharField(max_length=128)
    address_2 = forms.CharField(max_length=128, required=False)
    address_zip = forms.CharField(max_length=10)

    """ Admin fields """
    is_active           = forms.BooleanField(required=False)
    is_auto_password    = forms.BooleanField(required=False)

    date_created = forms.DateTimeField(required=False)
    date_confirmed = forms.DateTimeField(required=False)
    date_completed = forms.DateTimeField(required=False)

    # online_id = forms.IntegerField(required=False)

    def clean_gender(self):
        data = self.cleaned_data['gender']

        if data < 1 or data > 3:
            raise ValidationError('Genre invalide, doit être compris entre 1 et 3.')

        return data

    def clean_zip_code(self):
        data = self.cleaned_data['zip_code']

        if data not in CITIES:
            raise ValidationError('Code postal incorrect.')

        # self.cleaned_data['city'] = CITIES[data]

        return data

    


    class Meta:
        model = User