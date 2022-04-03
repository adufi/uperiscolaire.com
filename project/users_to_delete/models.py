import jwt

from enum import IntEnum
from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from datetime import datetime, timedelta

from .managers import CustomUserManager

# Create your models here.

""" Enums """
class UserEmailType(IntEnum):
    HOME = 1
    WORK = 2
    OTHER = 3

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class UserPhoneType(IntEnum):
    MAIN = 1
    HOME = 2
    HOME_CELL = 3
    HOME_FAX = 4
    WORK = 5
    WORK_CELL = 6
    WORK_FAX = 7
    OTHER = 8

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class UserAddressType(IntEnum):
    HOME = 1
    WORK = 2
    OTHER = 3

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class UserGenderEnum(IntEnum):
    UNSET   = 0
    MALE    = 1
    FEMALE  = 2
    TUTOR   = 3

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


""" Data Models """
class Role(models.Model):
    name = models.CharField(max_length=128, default='')
    slug = models.CharField(max_length=128, default='')

    def __str__(self):
        return '#{} - {} - {}'.format(self.id, self.name, self.slug)

    def to_json(self):
        return {
            'name': self.name,
            'slug': self.slug,
        }


class UserAuth(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    # password = models.CharField(max_length=255)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return '#{} - Auth with email ({}) '.format(self.id, self.email)

    @property
    def token(self):
        return self._encode_auth_token()

    def _encode_auth_token(self):
        """Generates the auth token"""
        try:
            payload = {
                'exp':
                    datetime.utcnow() + timedelta(
                        days=settings.TOKEN_EXPIRATION_DAYS,
                        seconds=settings.TOKEN_EXPIRATION_SECONDS
                    ),
                # 'iat': datetime.utcnow(),
                'id': self.id,
            }
            token = jwt.encode(
                payload,
                settings.SECRET_KEY,
                algorithm='HS256'
            )
            return token.decode('utf-8')
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token):
        """
        Decodes the auth token - :param auth_token: - :return: integer|string
        """
        try:
            payload = jwt.decode(
                auth_token, 
                settings.SECRET_KEY
            )
            return payload['id']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'

    """ Called by User.to_json() """

    def to_json_(self):
        return {
            'id': self.id,
            'email': self.email,
        }

    def to_json(self):
        return {
            'id': self.id,
            'email': self.email,
            'user': self.user.to_json_(),
        }


class User(models.Model):
    last_name = models.CharField(max_length=128, default='')
    first_name = models.CharField(max_length=128, default='')

    job = models.CharField(max_length=128, default='')
    gender = models.IntegerField(
        choices=UserGenderEnum.choices(), 
        default=UserGenderEnum.UNSET
    )

    slug = models.CharField(max_length=256, default='')

    dob = models.DateField(blank=True, null=True)
    birthplace = models.CharField(max_length=128, default='')

    """ Is account active / Is password created by admin """
    is_active           = models.BooleanField(default=True)
    is_auto_password    = models.BooleanField(default=False)

    accept_newsletter = models.BooleanField(default=False)

    """ Account creation date / Date email confirmed """
    date_created = models.DateTimeField(default=now)
    date_confirmed = models.DateTimeField(blank=True, null=True)
    date_completed = models.DateTimeField(blank=True, null=True)

    """ Child ID used for the migration """
    online_id = models.IntegerField(default=0)

    auth = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    roles = models.ManyToManyField(Role)

    class Meta:
        ordering = ['id']

    def set_slug(self):
        def purge_accents (strAccents):
            strAccents = list(strAccents)
            strAccentsOut = []
            accents = 'ÀÁÂÃÄÅàáâãäåÒÓÔÕÕÖØòóôõöøÈÉÊËèéêëðÇçÐÌÍÎÏìíîïÙÚÛÜùúûüÑñŠšŸÿýŽž'
            accentsOut = "AAAAAAaaaaaaOOOOOOOooooooEEEEeeeeeCcDIIIIiiiiUUUUuuuuNnSsYyyZz"
            for i, letter in enumerate(strAccents):
                index = accents.find(strAccents[i])
                if index != -1:
                    strAccentsOut.append(accentsOut[index])
                else:
                    strAccentsOut.append(strAccents[i])
                
            strAccentsOut = ''.join(strAccentsOut)
            return strAccentsOut

        raw = self.last_name + self.first_name
        raw = raw.lower()
        raw = raw.replace(' ', '')
        raw = raw.replace('-', '')

        self.slug = purge_accents(raw)
        self.save()        
        

    def to_json(self):
        blank_if_none = lambda x: '' if not x else x
        user = {
            'id':                   self.id,
            'online_id':            self.online_id,
            
            'dob':                  blank_if_none(self.dob),
            'birthplace':           self.birthplace,
            'job':                  self.job,
            'gender':               self.gender,
            'slug':                 self.slug,
            'last_name':            self.last_name,
            'first_name':           self.first_name,

            'is_active':            self.is_active,
            'is_auto_password':     self.is_auto_password,
            'accept_newsletter':    self.accept_newsletter,

            'date_created':         blank_if_none(self.date_created).__str__(),
            'date_confirmed':       blank_if_none(self.date_confirmed).__str__(),
            'date_completed':       blank_if_none(self.date_completed).__str__(),

            'email': '',
            'phones': '',
            'address': '',

            'auth':                 True if self.auth else False
        }

        # phone = self.phones.first()
        # if phone:
        #     user['phone'] = phone.to_json()['phone']
        #     # user['phone'] = PhoneSerializer(phone).data['phone']

        if hasattr(self, 'phones'):
            user['phones'] = self.phones.to_json()

        email = self.emails.first()
        if email:
            user['email'] = email.to_json()['email']
            # user['email'] = EmailSerializer(email).data['email']

        address = self.addresses.first()
        if address:
            # user['address'] = {
            #     'city': address.city,
            #     'address1': address.address1,
            #     'address2': address.address2,
            #     'zip_code': address.zip_code,
            # }
            user['address'] = address.to_json()
            # user['address'] = AddressSerializer(address).data

        roles = self.roles.all()
        if roles:
            user['roles'] = []
            for role in roles:
                user['roles'].append(role.to_json())

        return user

    def __str__(self):
        return '#{} - {} {} ({})'.format(self.id, self.first_name, self.last_name, self.dob)


class UserEmail(models.Model):
    is_main = models.BooleanField(default=False)

    email = models.CharField(
        null=False,
        blank=False,
        max_length=128,
    )

    email_type = models.IntegerField(
        default=UserEmailType.HOME,
        choices=UserEmailType.choices() 
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='emails'
    )

    def __str__(self):
        return '#{} - User ({}) with Email ({})'.format(self.id, self.user.id, self.email)

    def to_json(self):
        return {
            'email': self.email,
            'is_main': self.is_main,
            'email_type': self.email_type,
        }


class UserAddress(models.Model):
    is_main = models.BooleanField(default=False)
    
    name = models.CharField(max_length=128, default='')

    address_type = models.IntegerField(
        null=False,
        blank=False,
        choices=UserAddressType.choices(),
        default=UserAddressType.HOME
    )
    
    city = models.CharField(
        null=False,     
        blank=False,
        default='',
        max_length=128, 
    )
    address1 = models.CharField(
        null=False,     
        blank=False,
        default='',
        max_length=128, 
    )
    address2 = models.CharField(
        default='',
        max_length=128, 
    )
    zip_code = models.CharField(
        null=False,     
        blank=False,
        default='',
        max_length=12,  
    )
    country = models.CharField(
        default='Martinique',
        max_length=128, 
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses'
    )

    def __str__(self):
        return '#{} - User ({}) with Address name ({})'.format(self.id, self.user.id, self.name)

    def to_json(self):
        return {
            'name': self.name,
            'city': self.city,
            'country': self.country,
            'zip_code': self.zip_code,
            'address1': self.address1,
            'address2': self.address2,
            'is_main': self.is_main,
            'address_type': self.address_type,
        }


# Old
class UserPhone(models.Model):
    is_main = models.BooleanField(default=False)

    phone = models.CharField(
        null=False,
        blank=False,
        default='',
        max_length=20, 
    )

    phone_type = models.IntegerField(
        null=False,
        blank=False,
        choices=UserPhoneType.choices(),
        default=UserPhoneType.HOME,
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='_phones'
    )

    def __str__(self):
        return '#{} - User ({}) with Phone ({})'.format(self.id, self.user.id, self.phone)

    def to_json(self):
        return {
            'phone': self.phone,
            'is_main': self.is_main,
            'phone_type': self.phone_type,
        }


class UserPhones(models.Model):
    phone_cell = models.CharField(
        null=False,
        blank=False,
        default='',
        max_length=20, 
    )

    phone_home = models.CharField(
        null=False,
        blank=False,
        default='',
        max_length=20, 
    )

    phone_pro = models.CharField(
        null=False,
        blank=False,
        default='',
        max_length=20, 
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='phones'
    )

    def __str__(self):
        return 'Phones for User ({}) with Phones: {} - {} - {}'.format(self.id, self.user.id, self.phone_cell, self.cell_home, self.cell_pro)

    def to_json(self):
        return {
            'cell': self.phone_cell,
            'home': self.phone_home,
            'pro': self.phone_pro,
        }
