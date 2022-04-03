from enum import IntEnum
from django.db import models
from django.utils.timezone import now

# Create your models here.

""" Enums """
class UserGenderEnum(IntEnum):
    UNSET   = 0
    MALE    = 1
    FEMALE  = 2
    TUTOR   = 3

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class ChildClass(IntEnum):
    UNSET = 0
    STP = 1
    SP = 2
    SM = 3
    SG = 4
    CP = 5
    CE1 = 6
    CE2 = 7
    CM1 = 8
    CM2 = 9
    SIX = 10

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class ChildPAI(IntEnum):
    UNSET = 0
    NO = 1
    YES = 2
    ONGOING = 3

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class ChildQuotient(IntEnum):
    UNSET   = 0
    NE      = 1
    Q2      = 2
    Q1      = 3

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


""" Models """

""" Sibling as Parent """
class Sibling(models.Model):
    parent = models.IntegerField(default=0)

    def add_child(self, child):
        try:
            sibling = Sibling.objects.get(children__child=child) 
            sibling.remove_child(child)
        except Sibling.DoesNotExist:
            pass
        self.children.create(
            child=child,
            sibling=self
        )


    def remove_child(self, child):
        try:
            self.children.get(child=child).delete()
        except SiblingChild.DoesNotExist:
            return False
        return True
        

    def add_intels(self, intels, school_year):
        # Check intel unicity
        if self.intels.filter(school_year=school_year):
            return False

        return self.intels.create(
            quotient_1=intels.get('quotient_1', ChildQuotient.UNSET),
            quotient_2=intels.get('quotient_2', ChildQuotient.UNSET),
            recipent_number=intels.get('recipent_number', 0),
            # insurance_policy=intels.get('insurance_policy', 0),
            # insurance_society=intels.get('insurance_society', ''),
            school_year=school_year,
            sibling=self
        )

    
    def remove_intels(self, pk):
        try:
            self.intels.get(pk=pk).delete()
            return True
        except SiblingIntels.DoesNotExist:
            return False


    def to_json(self):
        return {
            'id': self.id,
            'parent': self.parent,

            'intels': [x.to_json() for x in self.intels.all()] if self.intels.all() else [],

            'children': [x.to_json() for x in self.children.all()] if self.children.all() else [],
        }

    def __str__(self):
        return '#{} - Sibling for parent: {}'.format(self.id, str(self.parent))


""" SiblingChild as Child """
class SiblingChild(models.Model):
    child = models.IntegerField(default=0)

    sibling = models.ForeignKey(
        Sibling,
        related_name='children',
        on_delete=models.CASCADE
    )

    # @property
    # def child_id(self):
    #     return self.child.id


    def to_json(self):
        return {
            'id': self.id,
            'child': self.child
        }


    def __str__(self):
        return '#{} - Sibling ({}) for child: ({})'.format(self.id, self.sibling.id, self.child)


class SiblingIntels(models.Model):
    quotient_1 = models.IntegerField(choices=ChildQuotient.choices(), default=ChildQuotient.NE)
    quotient_2 = models.IntegerField(choices=ChildQuotient.choices(), default=ChildQuotient.NE)

    recipent_number = models.IntegerField(default=0)

    # In Record now
    # insurance_policy = models.CharField(max_length=128, default=0)
    # insurance_society = models.CharField(max_length=128, default='')
    
    school_year = models.IntegerField(default=0)

    date_created = models.DateTimeField(default=now)
    date_last_mod = models.DateTimeField(default=now)
    date_verified = models.DateTimeField(blank=True, null=True)

    sibling = models.ForeignKey(
        Sibling,
        on_delete=models.CASCADE,
        related_name='intels'
    )

    class Meta:
        ordering = ['-school_year']

    def to_json(self):
        blank_if_none = lambda x: '' if not x else x
        return {
            'id': self.id,
            'quotient_1': self.quotient_1,
            'quotient_2': self.quotient_2,

            'recipent_number': self.recipent_number,
            # 'insurance_policy': self.insurance_policy,
            # 'insurance_society': self.insurance_society,
            
            'school_year': self.school_year,

            'date_created': blank_if_none(self.date_created.__str__()),
            'date_verified': blank_if_none(self.date_verified.__str__()),
            'date_last_mod': blank_if_none(self.date_last_mod.__str__()),
        }

    def __str__(self):
        return f'#{self.id} - Intels for sibling ({self.sibling.id}) - School Year: {self.school_year}'


class Family(models.Model):
    child = models.IntegerField(default=0)
    parent = models.IntegerField(default=0)

    def __str__(self):
        return f'#{self.id} - Child ID: {self.child} - Parent ID: {self.parent}'

    def to_json(self):
        return {
            'parent': self.parent,
            'child': self.child,
        }


class Record(models.Model):
    school = models.CharField(max_length=100, default='')
    classroom = models.IntegerField(choices=ChildClass.choices(), default=ChildClass.UNSET)

    agreement = models.BooleanField(default=False)

    accueil_mati = models.BooleanField(default=False)
    accueil_midi = models.BooleanField(default=False)
    accueil_merc = models.BooleanField(default=False)
    accueil_vacs = models.BooleanField(default=False)

    insurance_policy = models.CharField(max_length=128, default=0)
    insurance_society = models.CharField(max_length=128, default='')

    date_created = models.DateTimeField(default=now)
    date_last_mod = models.DateTimeField(default=now)
    date_verified = models.DateTimeField(blank=True, null=True)

    child = models.IntegerField(default=0)
    school_year = models.IntegerField(default=0)

    class Meta:
        ordering = ['-school_year']

    def to_json(self):
        blank_if_none = lambda x: '' if not x else x
        payload  = {
            'id':           self.id,
            'school':       self.school,
            'classroom':    self.classroom,
            # 'classroom':    ChildClass(self.classroom).name,

            'agreement':    self.agreement,

            'accueil_mati':   self.accueil_mati,
            'accueil_midi':   self.accueil_midi,
            'accueil_merc':   self.accueil_merc,
            'accueil_vacs':   self.accueil_vacs,

            'insurance_policy':   self.insurance_policy,
            'insurance_society':   self.insurance_society,

            'date_created': blank_if_none(self.date_created.__str__()),
            'date_verified': blank_if_none(self.date_verified.__str__()),
            'date_last_mod': blank_if_none(self.date_last_mod.__str__()),

            'health': self.health.to_json() if hasattr(self, 'health') else False,
            'diseases': self.diseases.to_json() if hasattr(self, 'diseases') else False,
            'authorizations': self.authorizations.to_json() if hasattr(self, 'authorizations') else False,

            'child': self.child,
            'school_year': self.school_year
        }

        responsible = self.responsibles.first()
        recuperaters = self.recuperaters.all()

        payload['responsible'] = responsible.to_json() if responsible else False            

        payload['recuperaters'] = [_.to_json() for _ in recuperaters] if recuperaters else False            

        return payload

    def __str__(self):
        return '#{} - Record for child ({}) - School Year ({})'.format(self.id, self.child, self.school_year)


# RecordHealth
class Health(models.Model):
    asthme = models.BooleanField(default=False)
    allergy_food = models.BooleanField(default=False)
    allergy_drug = models.BooleanField(default=False)

    allergy_food_details = models.TextField(default='', blank=True)
    allergy_drug_details = models.TextField(default='', blank=True)

    pai = models.IntegerField(choices=ChildPAI.choices(), default=ChildPAI.NO)
    pai_details = models.TextField(default='', blank=True)

    medical_treatment = models.BooleanField(default=False)
    vaccine_up_to_date = models.BooleanField(default=False)

    lunettes = models.BooleanField(default=False)
    lentilles = models.BooleanField(default=False)
    protheses_dentaire = models.BooleanField(default=False)
    protheses_auditives = models.BooleanField(default=False)

    autres_recommandations = models.TextField(default='', blank=True)

    doctor_names = models.CharField(max_length=128, default='')
    doctor_phones = models.CharField(max_length=128, default='') 

    record = models.OneToOneField(
        Record,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='health'
    )

    def to_json(self):
        return {
            # 'pai':                  ChildPAI(self.pai).name,
            'pai':                  self.pai,
            'asthme':               self.asthme,
            'allergy_food':         self.allergy_food,
            'allergy_drug':         self.allergy_drug,

            'pai_details':          self.pai_details,
            'allergy_food_details': self.allergy_food_details,
            'allergy_drug_details': self.allergy_drug_details,

            'medical_treatment':        self.medical_treatment,
            'vaccine_up_to_date':       self.vaccine_up_to_date,

            'lunettes':                 self.lunettes,
            'lentilles':                self.lentilles,
            'protheses_dentaire':       self.protheses_dentaire,
            'protheses_auditives':      self.protheses_auditives,

            'doctor_names':     self.doctor_names,
            'doctor_phones':    self.doctor_phones,
            
            'autres_recommandations':   self.autres_recommandations,
        }

    def __str__(self):
        return 'Health for record ({}) and child ({})'.format(self.record.id, self.record.child)


class RecordDiseases(models.Model):
    rubeole     = models.BooleanField(default=False)
    varicelle   = models.BooleanField(default=False)
    angine      = models.BooleanField(default=False)
    rhumatisme  = models.BooleanField(default=False)
    scarlatine  = models.BooleanField(default=False)
    coqueluche  = models.BooleanField(default=False)
    otite       = models.BooleanField(default=False)
    rougeole    = models.BooleanField(default=False)
    oreillons   = models.BooleanField(default=False)

    record = models.OneToOneField(
        Record,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='diseases'
    )

    def to_json(self):
        return {
            'rubeole': self.rubeole,
            'varicelle': self.varicelle,
            'angine': self.angine,
            'rhumatisme': self.rhumatisme,
            'scarlatine': self.scarlatine,
            'coqueluche': self.coqueluche,
            'otite': self.otite,
            'rougeole': self.rougeole,
            'oreillons': self.oreillons
        }

    def __str__(self):
        return 'Diseases for Record ({})'.format(self.record.id)


class RecordResponsible(models.Model):
    last_name = models.CharField(max_length=128, default='', blank=True)
    first_name = models.CharField(max_length=128, default='', blank=True)

    job = models.CharField(max_length=128, default='', blank=True)
    gender = models.IntegerField(choices=UserGenderEnum.choices(), default=UserGenderEnum.UNSET)

    email = models.CharField(max_length=128, default='', blank=True)

    phone_cell = models.CharField(max_length=128, default='', blank=True)
    phone_home = models.CharField(max_length=128, default='', blank=True)
    phone_pro = models.CharField(max_length=128, default='', blank=True)

    address_zip = models.CharField(max_length=128, default='', blank=True)
    address_city = models.CharField(max_length=128, default='', blank=True)
    address_address1 = models.CharField(max_length=128, default='', blank=True)
    address_address2 = models.CharField(max_length=128, default='', blank=True)

    record = models.ForeignKey(
        Record,
        on_delete=models.CASCADE,
        related_name='responsibles'
    )

    def to_json(self):
        return {
            'id':               self.id,
            'last_name':        self.last_name,
            'first_name':       self.first_name,
            'job':              self.job,
            'gender':           self.gender,
            'email':            self.email,
            'phone_cell':       self.phone_cell,
            'phone_home':       self.phone_home,
            'phone_pro':        self.phone_pro,
            'address_zip':      self.address_zip,
            'address_city':     self.address_city,
            'address_address1': self.address_address1,
            'address_address2': self.address_address2,
        }

    def __str__(self):
        return '#{} - Responsible: {} {} of Record ({})'.format(self.id, self.last_name, self.first_name, self.record.id)


class RecordRecuperater(models.Model):
    names = models.CharField(max_length=128, default='', blank=True)
    phones = models.CharField(max_length=128, default='', blank=True)
    quality = models.CharField(max_length=128, default='', blank=True)

    record = models.ForeignKey(
        Record,
        on_delete=models.CASCADE,
        related_name='recuperaters'
    )

    def to_json(self):
        return {
            'id': self.id,
            'names': self.names,
            'phones': self.phones,
            'quality': self.quality
        }

    def __str__(self):
        return '#{} - Recuperater: {} {} {} of Record ({})'.format(self.id, self.names, self.phones, self.quality, self.record.id)


class RecordAuthorizations(models.Model):
    bath = models.BooleanField(default=False)
    image = models.BooleanField(default=False)
    sport = models.BooleanField(default=False)
    transport = models.BooleanField(default=False)
    medical_transport = models.BooleanField(default=False)

    record = models.OneToOneField(
        Record,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='authorizations'
    )

    def to_json(self):
        return {
            'bath': self.bath,
            'image': self.image,
            'sport': self.sport,
            'transport': self.transport,
            'medical_transport': self.medical_transport,
        }

    def __str__(self):
        return 'Authorizations for Record ({})'.format(self.record.id) 


# Not used
class CAF(models.Model):
    # Quarter 1 and 2
    q1 = models.IntegerField(choices=ChildQuotient.choices(), default=ChildQuotient.NE)
    q2 = models.IntegerField(choices=ChildQuotient.choices(), default=ChildQuotient.NE)
    
    recipent_number = models.IntegerField(default=0)

    # record = models.OneToOneField(
    #     Record,
    #     on_delete=models.CASCADE,
    #     primary_key=True,
    #     related_name='caf'
    # )

    def __str__(self):
        return 'CAF for record ({}) and child ({})'.format(self.record.id, self.record.user_id)

