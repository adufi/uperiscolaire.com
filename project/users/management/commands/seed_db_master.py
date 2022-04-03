import json
from datetime import datetime
from django.core.management.base import BaseCommand

from order.models import Order, OrderMethod, OrderStatus, Ticket, TicketStatus, MethodEnum, StatusEnum, Client, ClientCredit
from users.models import User, UserAuth, Role, UserEmail, UserPhone, UserAddress, UserEmailType
from params.models import Product, ProductStock, SchoolYear, CategoryEnum, SubCategoryEnum
from registration.models import Sibling, SiblingChild, SiblingIntels, Record, Health, ChildPAI, ChildClass, ChildQuotient, RecordAuthorizations, RecordDiseases, RecordRecuperater, RecordResponsible


class Command(BaseCommand):
    help = 'Seed our DB'

    def create_users(self):
        def clean():
            User.objects.filter(id__gte=2).delete()
            UserAuth.objects.filter(id__gte=2).delete()
            Role.objects.all().delete()
            UserEmail.objects.all().delete()
            UserPhone.objects.all().delete()
            UserAddress.objects.all().delete()

        def create_role(name, slug):
            return Role.objects.create(
                name=name,
                slug=slug
            )

        def create_user(first_name, last_name, role, dob=None, email=None):
            u = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                dob=dob
            )
            u.roles.add(role)
            if email:
                u.emails.create(
                    email=email,
                    email_type=UserEmailType.HOME,
                    is_main=True,
                )
            return u

        def create_auth(email, password):
            return UserAuth.objects.create_user(
                email=email,
                password=password
            )

        def create_full_user(first_name, last_name, email, password, role):
            user = create_user(
                first_name=first_name,
                last_name=last_name, 
                email=email, 
                role=role
            )
            user.auth = create_auth(email, password)
            user.save()
            return user

        def alter_superuser():
            try:
                user = User.objects.create()
                user.auth = UserAuth.objects.get(pk=1)
                user.save()
            except UserAuth.DoesNotExist:
                return False
            return True

        def core():
            r_adm = create_role('Admin', 'admin')
            r_chi = create_role('Child', 'child')
            r_par = create_role('Parent', 'parent')
            r_apa = create_role('AP admin', 'ap_admin')

            if not alter_superuser():
                print ('Superuser alteration failed')

            """ Sys Admin """
            self.user_sys = create_full_user(
                first_name='Sys',
                last_name='Admin',
                email='sys.admin@mail.fr',
                password='password',
                role=r_adm
            )

            """ AP Admin """
            self.user_ap = create_full_user(
                first_name='AP',
                last_name='Admin',
                email='ap.admin@mail.fr',
                password='password',
                role=r_apa
            )

            """ Parent """
            self.user_parent = create_full_user(
                first_name='Parent',
                last_name='Test',
                email='parent@mail.fr',
                password='password',
                role=r_par
            )

            """ Child 1 """
            self.user_child_1 = create_user(
                first_name='Child 1',
                last_name='Test',
                dob='2017-06-01',
                role=r_chi
            )

            """ Child 2 """
            self.user_child_2 = create_user(
                first_name='Child 2',
                last_name='Test',
                dob='2015-03-01',
                role=r_chi
            )

            """ Child 3 """
            self.user_child_3 = create_user(
                first_name='Child 3',
                last_name='Test',
                dob='2014-03-01',
                role=r_chi
            )

        clean()
        core()


    def create_records(self):
        def clean():
            Sibling.objects.all().delete()
            SiblingChild.objects.all().delete()
            SiblingIntels.objects.all().delete()
            
            Record.objects.all().delete()
            Health.objects.all().delete()

        def create_record(child_id, _record):
            record = Record.objects.create(
                child=child_id,
                school=_record['school'],
                classroom=_record['classroom'],
                school_year=self.s1.id
            )
            Health.objects.create(record=record)

            return record

        def create_sibling_child(child):
            self.sibling.children.add(
                SiblingChild.objects.create(
                    child=child,
                    sibling=self.sibling
                )
            )

        def core():
            # child_1 = Child.objects.create(id=self.user_child_1.id, user=self.user_child_1.id)
            # child_2 = Child.objects.create(id=self.user_child_2.id, user=self.user_child_2.id)
            # child_3 = Child.objects.create(id=self.user_child_3.id, user=self.user_child_3.id)

            # Create sibling
            self.sibling = Sibling.objects.create(parent=self.user_parent.id)

            # Add children
            create_sibling_child(self.user_child_1.id)
            create_sibling_child(self.user_child_2.id)
            create_sibling_child(self.user_child_3.id)

            # Add intels
            self.sibling.intels.create(
                quotient_1=ChildQuotient.Q1,
                quotient_2=ChildQuotient.Q2,
                recipent_number=0,
                # insurance_policy=0,
                school_year=self.s1.id,
                sibling=self.sibling,
            )
            
            create_record(self.user_child_1.id, {
                'school': 'CHAP',
                'classroom': ChildClass.SM
            })

            create_record(self.user_child_2.id, {
                'school': 'BDP',
                'classroom': ChildClass.SP
            })

            create_record(self.user_child_3.id, {
                'school': 'HM',
                'classroom': ChildClass.CP
            })
        
        clean()
        core()
    

    def create_params(self):
        def clean():
            Product.objects.all().delete()
            SchoolYear.objects.all().delete()

        def create_product(id, name, slug, description, order, date, category, subcategory, stock, price, price_q1, price_q2, date_start, date_end, school_year):
            product = Product.objects.create(
                id=id,
                name=name,
                slug=slug,
                description=description,
                order=order,
                date=date,
                category=category,
                subcategory=subcategory,
                # stock=stock,
                price=price,
                price_q1=price_q1,
                price_q2=price_q2,
                date_start=date_start,
                date_end=date_end,
                school_year=school_year,

                stock_max=stock,
                stock_current=0
            )
            # product.stock = ProductStock.objects.create(
            #     max=stock,
            #     product=product
            # )
            return product

        def create_school_year(date_start, date_end, is_active=False):
            return SchoolYear.objects.create(
                date_start=date_start,
                date_end=date_end,
                is_active=is_active
            )

        def create_products_s1(sy):
            raw = [
                '0,Septembre,sept_2019x2020,,1,,PERI,,,20,,',
                '1,Octobre,octo_2019x2020,,2,,PERI,,,20,,',
                '2,Novembre,nove_2019x2020,,3,,PERI,,,20,,',
                '3,Décembre,dece_2019x2020,,4,,PERI,,,20,,',
                '4,Janvier,janv_2019x2020,,5,,PERI,,,20,,',
                '5,Février,fevr_2019x2020,,6,,PERI,,,20,,',
                '6,Mars,mars_2019x2020,,7,,PERI,,,20,,',
                '7,Avril,avri_2019x2020,,8,,PERI,,,20,,',
                '8,Mai,mai_2019x2020,,9,,PERI,,,20,,',
                '9,Juin,juin_2019x2020,,10,,PERI,,,20,,',
                '10,Juillet,juil_2019x2020,,11,,PERI,,,20,,',
                '10,Mercredi 04 Septembre,merc_04_08_m6_2019x2020,,,04/09/2019,SEPTEMBRE,MINUS6,104,17,4,0',
                '11,Mercredi 04 Septembre,merc_04_08_p6_2019x2020,,,04/09/2019,SEPTEMBRE,PLUS6,100,20,7,2',
                '12,Mercredi 11 Septembre,merc_11_08_m6_2019x2020,,,11/09/2019,SEPTEMBRE,MINUS6,104,17,4,0',
                '13,Mercredi 11 Septembre,merc_11_08_p6_2019x2020,,,11/09/2019,SEPTEMBRE,PLUS6,100,20,7,2',
                '14,Mercredi 18 Septembre,merc_18_08_m6_2019x2020,,,18/09/2019,SEPTEMBRE,MINUS6,104,17,4,0',
                '15,Mercredi 18 Septembre,merc_18_08_p6_2019x2020,,,18/09/2019,SEPTEMBRE,PLUS6,100,20,7,2',
                '16,Mercredi 25 Septembre,merc_25_08_m6_2019x2020,,,25/09/2019,SEPTEMBRE,MINUS6,104,17,4,0',
                '17,Mercredi 25 Septembre,merc_25_08_p6_2019x2020,,,25/09/2019,SEPTEMBRE,PLUS6,100,20,7,2',
                '18,Mercredi 02 Octobre,merc_02_09_m6_2019x2020,,,02/10/2019,OCTOBRE,MINUS6,104,17,4,0',
                '19,Mercredi 02 Octobre,merc_02_09_p6_2019x2020,,,02/10/2019,OCTOBRE,PLUS6,100,20,7,2',
                '20,Mercredi 09 Octobre,merc_09_09_m6_2019x2020,,,09/10/2019,OCTOBRE,MINUS6,104,17,4,0',
                '21,Mercredi 09 Octobre,merc_09_09_p6_2019x2020,,,09/10/2019,OCTOBRE,PLUS6,100,20,7,2',
                '22,Mercredi 16 Octobre,merc_16_09_m6_2019x2020,,,16/10/2019,OCTOBRE,MINUS6,104,17,4,0',
                '23,Mercredi 16 Octobre,merc_16_09_p6_2019x2020,,,16/10/2019,OCTOBRE,PLUS6,100,20,7,2',
                '24,Mercredi 06 Novembre,merc_06_10_m6_2019x2020,,,06/11/2019,NOVEMBRE,MINUS6,104,17,4,0',
                '25,Mercredi 06 Novembre,merc_06_10_p6_2019x2020,,,06/11/2019,NOVEMBRE,PLUS6,100,20,7,2',
                '26,Mercredi 13 Novembre,merc_13_10_m6_2019x2020,,,13/11/2019,NOVEMBRE,MINUS6,104,17,4,0',
                '27,Mercredi 13 Novembre,merc_13_10_p6_2019x2020,,,13/11/2019,NOVEMBRE,PLUS6,100,20,7,2',
                '28,Mercredi 20 Novembre,merc_20_10_m6_2019x2020,,,20/11/2019,NOVEMBRE,MINUS6,104,17,4,0',
                '29,Mercredi 20 Novembre,merc_20_10_p6_2019x2020,,,20/11/2019,NOVEMBRE,PLUS6,100,20,7,2',
                '30,Mercredi 27 Novembre,merc_27_10_m6_2019x2020,,,27/11/2019,NOVEMBRE,MINUS6,104,17,4,0',
                '31,Mercredi 27 Novembre,merc_27_10_p6_2019x2020,,,27/11/2019,NOVEMBRE,PLUS6,100,20,7,2',
                '32,Mercredi 04 Décembre,merc_04_11_m6_2019x2020,,,04/12/2019,DECEMBRE,MINUS6,104,17,4,0',
                '33,Mercredi 04 Décembre,merc_04_11_p6_2019x2020,,,04/12/2019,DECEMBRE,PLUS6,100,20,7,2',
                '34,Mercredi 11 Décembre,merc_11_11_m6_2019x2020,,,11/12/2019,DECEMBRE,MINUS6,104,17,4,0',
                '35,Mercredi 11 Décembre,merc_11_11_p6_2019x2020,,,11/12/2019,DECEMBRE,PLUS6,100,20,7,2',
                '36,Mercredi 18 Décembre,merc_18_11_m6_2019x2020,,,18/12/2019,DECEMBRE,MINUS6,104,17,4,0',
                '37,Mercredi 18 Décembre,merc_18_11_p6_2019x2020,,,18/12/2019,DECEMBRE,PLUS6,100,20,7,2',
                '38,Lundi 21 Octobre,lund_21_09_m6_2019x2020,,,21/10/2019,TOUSSAINT,MINUS6,104,17,4,0',
                '39,Lundi 21 Octobre,lund_21_09_p6_2019x2020,,,21/10/2019,TOUSSAINT,PLUS6,100,20,7,2',
                '40,Mardi 22 Octobre,mard_22_09_m6_2019x2020,,,22/10/2019,TOUSSAINT,MINUS6,104,17,4,0',
                '41,Mardi 22 Octobre,mard_22_09_p6_2019x2020,,,22/10/2019,TOUSSAINT,PLUS6,100,20,7,2',
                '42,Mercredi 23 Octobre,merc_23_09_m6_2019x2020,,,23/10/2019,TOUSSAINT,MINUS6,104,17,4,0',
                '43,Mercredi 23 Octobre,merc_23_09_p6_2019x2020,,,23/10/2019,TOUSSAINT,PLUS6,100,20,7,2',
                '44,Jeudi 24 Octobre,jeud_24_09_m6_2019x2020,,,24/10/2019,TOUSSAINT,MINUS6,104,17,4,0',
                '45,Jeudi 24 Octobre,jeud_24_09_p6_2019x2020,,,24/10/2019,TOUSSAINT,PLUS6,100,20,7,2',
                '46,Vendredi 25 Octobre,vend_25_09_m6_2019x2020,,,25/10/2019,TOUSSAINT,MINUS6,104,17,4,0',
                '47,Vendredi 25 Octobre,vend_25_09_p6_2019x2020,,,25/10/2019,TOUSSAINT,PLUS6,100,20,7,2',
                '48,Lundi 28 Octobre,lund_28_09_m6_2019x2020,,,28/10/2019,TOUSSAINT,MINUS6,104,17,4,0',
                '49,Lundi 28 Octobre,lund_28_09_p6_2019x2020,,,28/10/2019,TOUSSAINT,PLUS6,100,20,7,2',
                '50,Mardi 29 Octobre,mard_29_09_m6_2019x2020,,,29/10/2019,TOUSSAINT,MINUS6,104,17,4,0',
                '51,Mardi 29 Octobre,mard_29_09_p6_2019x2020,,,29/10/2019,TOUSSAINT,PLUS6,100,20,7,2',
                '52,Mercredi 30 Octobre,merc_30_09_m6_2019x2020,,,30/10/2019,TOUSSAINT,MINUS6,104,17,4,0',
                '53,Mercredi 30 Octobre,merc_30_09_p6_2019x2020,,,30/10/2019,TOUSSAINT,PLUS6,100,20,7,2',
                '54,Jeudi 31 Octobre,jeud_31_09_m6_2019x2020,,,31/10/2019,TOUSSAINT,MINUS6,104,17,4,0',
                '55,Jeudi 31 Octobre,jeud_31_09_p6_2019x2020,,,31/10/2019,TOUSSAINT,PLUS6,100,20,7,2',
                '56,Lundi 23 Décembre,lund_23_11_m6_2019x2020,,,23/12/2019,NOEL,MINUS6,104,17,4,0',
                '57,Lundi 23 Décembre,lund_23_11_p6_2019x2020,,,23/12/2019,NOEL,PLUS6,100,20,7,2',
                '58,Mardi 24 Décembre,mard_24_11_m6_2019x2020,,,24/12/2019,NOEL,MINUS6,104,17,4,0',
                '59,Mardi 24 Décembre,mard_24_11_p6_2019x2020,,,24/12/2019,NOEL,PLUS6,100,20,7,2',
                '60,Jeudi 26 Décembre,jeud_26_11_m6_2019x2020,,,26/12/2019,NOEL,MINUS6,104,17,4,0',
                '61,Jeudi 26 Décembre,jeud_26_11_p6_2019x2020,,,26/12/2019,NOEL,PLUS6,100,20,7,2',
                '62,Vendredi 27 Décembre,vend_27_11_m6_2019x2020,,,27/12/2019,NOEL,MINUS6,104,17,4,0',
                '63,Vendredi 27 Décembre,vend_27_11_p6_2019x2020,,,27/12/2019,NOEL,PLUS6,100,20,7,2',
                '64,Lundi 30 Décembre,lund_30_11_m6_2019x2020,,,30/12/2019,NOEL,MINUS6,104,17,4,0',
                '65,Lundi 30 Décembre,lund_30_11_p6_2019x2020,,,30/12/2019,NOEL,PLUS6,100,20,7,2',
                '66,Mardi 31 Décembre,mard_31_11_m6_2019x2020,,,31/12/2019,NOEL,MINUS6,104,17,4,0',
                '67,Mardi 31 Décembre,mard_31_11_p6_2019x2020,,,31/12/2019,NOEL,PLUS6,100,20,7,2',
                '68,Jeudi 02 Janvier,jeud_02_00_m6_2019x2020,,,02/01/2020,NOEL,MINUS6,104,17,4,0',
                '69,Jeudi 02 Janvier,jeud_02_00_p6_2019x2020,,,02/01/2020,NOEL,PLUS6,100,20,7,2',
                '70,Vendredi 03 Janvier,vend_03_00_m6_2019x2020,,,03/01/2020,NOEL,MINUS6,104,17,4,0',
                '71,Vendredi 03 Janvier,vend_03_00_p6_2019x2020,,,03/01/2020,NOEL,PLUS6,100,20,7,2',
                '72,Mercredi 08 Janvier,merc_08_00_m6_2019x2020,,,08/01/2020,JANVIER,MINUS6,104,17,4,0',
                '73,Mercredi 08 Janvier,merc_08_00_p6_2019x2020,,,08/01/2020,JANVIER,PLUS6,100,20,7,2',
                '74,Mercredi 15 Janvier,merc_15_00_m6_2019x2020,,,15/01/2020,JANVIER,MINUS6,104,17,4,0',
                '75,Mercredi 15 Janvier,merc_15_00_p6_2019x2020,,,15/01/2020,JANVIER,PLUS6,100,20,7,2',
                '76,Mercredi 22 Janvier,merc_22_00_m6_2019x2020,,,22/01/2020,JANVIER,MINUS6,104,17,4,0',
                '77,Mercredi 22 Janvier,merc_22_00_p6_2019x2020,,,22/01/2020,JANVIER,PLUS6,100,20,7,2',
                '78,Mercredi 29 Janvier,merc_29_00_m6_2019x2020,,,29/01/2020,JANVIER,MINUS6,104,17,4,0',
                '79,Mercredi 29 Janvier,merc_29_00_p6_2019x2020,,,29/01/2020,JANVIER,PLUS6,100,20,7,2',
                '80,Mercredi 05 Février,merc_05_01_m6_2019x2020,,,05/02/2020,FEVRIER,MINUS6,104,17,4,0',
                '81,Mercredi 05 Février,merc_05_01_p6_2019x2020,,,05/02/2020,FEVRIER,PLUS6,100,20,7,2',
                '82,Mercredi 12 Février,merc_12_01_m6_2019x2020,,,12/02/2020,FEVRIER,MINUS6,104,17,4,0',
                '83,Mercredi 12 Février,merc_12_01_p6_2019x2020,,,12/02/2020,FEVRIER,PLUS6,100,20,7,2',
                '84,Mercredi 19 Février,merc_19_01_m6_2019x2020,,,19/02/2020,FEVRIER,MINUS6,104,17,4,0',
                '85,Mercredi 19 Février,merc_19_01_p6_2019x2020,,,19/02/2020,FEVRIER,PLUS6,100,20,7,2',
                '86,Mercredi 11 Mars,merc_11_02_m6_2019x2020,,,11/03/2020,MARS,MINUS6,104,17,4,0',
                '87,Mercredi 11 Mars,merc_11_02_p6_2019x2020,,,11/03/2020,MARS,PLUS6,100,20,7,2',
                '88,Mercredi 18 Mars,merc_18_02_m6_2019x2020,,,18/03/2020,MARS,MINUS6,104,17,4,0',
                '89,Mercredi 18 Mars,merc_18_02_p6_2019x2020,,,18/03/2020,MARS,PLUS6,100,20,7,2',
                '90,Mercredi 25 Mars,merc_25_02_m6_2019x2020,,,25/03/2020,MARS,MINUS6,104,17,4,0',
                '91,Mercredi 25 Mars,merc_25_02_p6_2019x2020,,,25/03/2020,MARS,PLUS6,100,20,7,2',
                '92,Mercredi 01 Avril,merc_01_03_m6_2019x2020,,,01/04/2020,AVRIL,MINUS6,104,17,4,0',
                '93,Mercredi 01 Avril,merc_01_03_p6_2019x2020,,,01/04/2020,AVRIL,PLUS6,100,20,7,2',
                '94,Mercredi 22 Avril,merc_22_03_m6_2019x2020,,,22/04/2020,AVRIL,MINUS6,104,17,4,0',
                '95,Mercredi 22 Avril,merc_22_03_p6_2019x2020,,,22/04/2020,AVRIL,PLUS6,100,20,7,2',
                '96,Mercredi 29 Avril,merc_29_03_m6_2019x2020,,,29/04/2020,AVRIL,MINUS6,104,17,4,0',
                '97,Mercredi 29 Avril,merc_29_03_p6_2019x2020,,,29/04/2020,AVRIL,PLUS6,100,20,7,2',
                '98,Mercredi 06 Mai,merc_06_04_m6_2019x2020,,,06/05/2020,MAI,MINUS6,104,17,4,0',
                '99,Mercredi 06 Mai,merc_06_04_p6_2019x2020,,,06/05/2020,MAI,PLUS6,100,20,7,2',
                '100,Mercredi 13 Mai,merc_13_04_m6_2019x2020,,,13/05/2020,MAI,MINUS6,104,17,4,0',
                '101,Mercredi 13 Mai,merc_13_04_p6_2019x2020,,,13/05/2020,MAI,PLUS6,100,20,7,2',
                '102,Mercredi 20 Mai,merc_20_04_m6_2019x2020,,,20/05/2020,MAI,MINUS6,104,17,4,0',
                '103,Mercredi 20 Mai,merc_20_04_p6_2019x2020,,,20/05/2020,MAI,PLUS6,100,20,7,2',
                '104,Mercredi 27 Mai,merc_27_04_m6_2019x2020,,,27/05/2020,MAI,MINUS6,104,17,4,0',
                '105,Mercredi 27 Mai,merc_27_04_p6_2019x2020,,,27/05/2020,MAI,PLUS6,100,20,7,2',
                '106,Mercredi 03 Juin,merc_03_05_m6_2019x2020,,,03/06/2020,JUIN,MINUS6,104,17,4,0',
                '107,Mercredi 03 Juin,merc_03_05_p6_2019x2020,,,03/06/2020,JUIN,PLUS6,100,20,7,2',
                '108,Mercredi 10 Juin,merc_10_05_m6_2019x2020,,,10/06/2020,JUIN,MINUS6,104,17,4,0',
                '109,Mercredi 10 Juin,merc_10_05_p6_2019x2020,,,10/06/2020,JUIN,PLUS6,100,20,7,2',
                '110,Mercredi 17 Juin,merc_17_05_m6_2019x2020,,,17/06/2020,JUIN,MINUS6,104,17,4,0',
                '111,Mercredi 17 Juin,merc_17_05_p6_2019x2020,,,17/06/2020,JUIN,PLUS6,100,20,7,2',
                '112,Mercredi 24 Juin,merc_24_05_m6_2019x2020,,,24/06/2020,JUIN,MINUS6,104,17,4,0',
                '113,Mercredi 24 Juin,merc_24_05_p6_2019x2020,,,24/06/2020,JUIN,PLUS6,100,20,7,2',
                '114,Mercredi 01 Juillet,merc_01_06_m6_2019x2020,,,01/07/2020,JUILLET,MINUS6,104,17,4,0',
                '115,Mercredi 01 Juillet,merc_01_06_p6_2019x2020,,,01/07/2020,JUILLET,PLUS6,100,20,7,2',
                '116,Jeudi 27 Février,jeud_27_01_m6_2019x2020,,,27/02/2020,CARNAVAL,MINUS6,104,17,4,0',
                '117,Jeudi 27 Février,jeud_27_01_p6_2019x2020,,,27/02/2020,CARNAVAL,PLUS6,100,20,7,2',
                '118,Vendredi 28 Février,vend_28_01_m6_2019x2020,,,28/02/2020,CARNAVAL,MINUS6,104,17,4,0',
                '119,Vendredi 28 Février,vend_28_01_p6_2019x2020,,,28/02/2020,CARNAVAL,PLUS6,100,20,7,2',
                '120,Lundi 02 Mars,lund_02_02_m6_2019x2020,,,02/03/2020,CARNAVAL,MINUS6,104,17,4,0',
                '121,Lundi 02 Mars,lund_02_02_p6_2019x2020,,,02/03/2020,CARNAVAL,PLUS6,100,20,7,2',
                '122,Mardi 03 Mars,mard_03_02_m6_2019x2020,,,03/03/2020,CARNAVAL,MINUS6,104,17,4,0',
                '123,Mardi 03 Mars,mard_03_02_p6_2019x2020,,,03/03/2020,CARNAVAL,PLUS6,100,20,7,2',
                '124,Mercredi 04 Mars,merc_04_02_m6_2019x2020,,,04/03/2020,CARNAVAL,MINUS6,104,17,4,0',
                '125,Mercredi 04 Mars,merc_04_02_p6_2019x2020,,,04/03/2020,CARNAVAL,PLUS6,100,20,7,2',
                '126,Jeudi 05 Mars,jeud_05_02_m6_2019x2020,,,05/03/2020,CARNAVAL,MINUS6,104,17,4,0',
                '127,Jeudi 05 Mars,jeud_05_02_p6_2019x2020,,,05/03/2020,CARNAVAL,PLUS6,100,20,7,2',
                '128,Vendredi 06 Mars,vend_06_02_m6_2019x2020,,,06/03/2020,CARNAVAL,MINUS6,104,17,4,0',
                '129,Vendredi 06 Mars,vend_06_02_p6_2019x2020,,,06/03/2020,CARNAVAL,PLUS6,100,20,7,2',
                '130,Lundi 06 Avril,lund_06_03_m6_2019x2020,,,06/04/2020,PAQUES,MINUS6,104,17,4,0',
                '131,Lundi 06 Avril,lund_06_03_p6_2019x2020,,,06/04/2020,PAQUES,PLUS6,100,20,7,2',
                '132,Mardi 07 Avril,mard_07_03_m6_2019x2020,,,07/04/2020,PAQUES,MINUS6,104,17,4,0',
                '133,Mardi 07 Avril,mard_07_03_p6_2019x2020,,,07/04/2020,PAQUES,PLUS6,100,20,7,2',
                '134,Mercredi 08 Avril,merc_08_03_m6_2019x2020,,,08/04/2020,PAQUES,MINUS6,104,17,4,0',
                '135,Mercredi 08 Avril,merc_08_03_p6_2019x2020,,,08/04/2020,PAQUES,PLUS6,100,20,7,2',
                '136,Jeudi 09 Avril,jeud_09_03_m6_2019x2020,,,09/04/2020,PAQUES,MINUS6,104,17,4,0',
                '137,Jeudi 09 Avril,jeud_09_03_p6_2019x2020,,,09/04/2020,PAQUES,PLUS6,100,20,7,2',
                '138,Mardi 14 Avril,mard_14_03_m6_2019x2020,,,14/04/2020,PAQUES,MINUS6,104,17,4,0',
                '139,Mardi 14 Avril,mard_14_03_p6_2019x2020,,,14/04/2020,PAQUES,PLUS6,100,20,7,2',
                '140,Mercredi 15 Avril,merc_15_03_m6_2019x2020,,,15/04/2020,PAQUES,MINUS6,104,17,4,0',
                '141,Mercredi 15 Avril,merc_15_03_p6_2019x2020,,,15/04/2020,PAQUES,PLUS6,100,20,7,2',
                '142,Jeudi 16 Avril,jeud_16_03_m6_2019x2020,,,16/04/2020,PAQUES,MINUS6,104,17,4,0',
                '143,Jeudi 16 Avril,jeud_16_03_p6_2019x2020,,,16/04/2020,PAQUES,PLUS6,100,20,7,2',
                '144,Vendredi 17 Avril,vend_17_03_m6_2019x2020,,,17/04/2020,PAQUES,MINUS6,104,17,4,0',
                '145,Vendredi 17 Avril,vend_17_03_p6_2019x2020,,,17/04/2020,PAQUES,PLUS6,100,20,7,2',
                '146,Lundi 06 Juillet,lund_06_06_m6_2019x2020,,,06/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '147,Lundi 06 Juillet,lund_06_06_p6_2019x2020,,,06/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '148,Mardi 07 Juillet,mard_07_06_m6_2019x2020,,,07/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '149,Mardi 07 Juillet,mard_07_06_p6_2019x2020,,,07/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '150,Mercredi 08 Juillet,merc_08_06_m6_2019x2020,,,08/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '151,Mercredi 08 Juillet,merc_08_06_p6_2019x2020,,,08/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '152,Jeudi 09 Juillet,jeud_09_06_m6_2019x2020,,,09/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '153,Jeudi 09 Juillet,jeud_09_06_p6_2019x2020,,,09/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '154,Vendredi 10 Juillet,vend_10_06_m6_2019x2020,,,10/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '155,Vendredi 10 Juillet,vend_10_06_p6_2019x2020,,,10/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '156,Lundi 13 Juillet,lund_13_06_m6_2019x2020,,,13/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '157,Lundi 13 Juillet,lund_13_06_p6_2019x2020,,,13/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '158,Mercredi 15 Juillet,merc_15_06_m6_2019x2020,,,15/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '159,Mercredi 15 Juillet,merc_15_06_p6_2019x2020,,,15/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '160,Jeudi 16 Juillet,jeud_16_06_m6_2019x2020,,,16/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '161,Jeudi 16 Juillet,jeud_16_06_p6_2019x2020,,,16/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '162,Vendredi 17 Juillet,vend_17_06_m6_2019x2020,,,17/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '163,Vendredi 17 Juillet,vend_17_06_p6_2019x2020,,,17/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '164,Lundi 20 Juillet,lund_20_06_m6_2019x2020,,,20/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '165,Lundi 20 Juillet,lund_20_06_p6_2019x2020,,,20/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '166,Mardi 21 Juillet,mard_21_06_m6_2019x2020,,,21/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '167,Mardi 21 Juillet,mard_21_06_p6_2019x2020,,,21/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '168,Mercredi 22 Juillet,merc_22_06_m6_2019x2020,,,22/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '169,Mercredi 22 Juillet,merc_22_06_p6_2019x2020,,,22/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '170,Jeudi 23 Juillet,jeud_23_06_m6_2019x2020,,,23/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '171,Jeudi 23 Juillet,jeud_23_06_p6_2019x2020,,,23/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '172,Vendredi 24 Juillet,vend_24_06_m6_2019x2020,,,24/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '173,Vendredi 24 Juillet,vend_24_06_p6_2019x2020,,,24/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '174,Lundi 27 Juillet,lund_27_06_m6_2019x2020,,,27/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '175,Lundi 27 Juillet,lund_27_06_p6_2019x2020,,,27/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '176,Mardi 28 Juillet,mard_28_06_m6_2019x2020,,,28/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '177,Mardi 28 Juillet,mard_28_06_p6_2019x2020,,,28/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '178,Mercredi 29 Juillet,merc_29_06_m6_2019x2020,,,29/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '179,Mercredi 29 Juillet,merc_29_06_p6_2019x2020,,,29/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '180,Jeudi 30 Juillet,jeud_30_06_m6_2019x2020,,,30/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '181,Jeudi 30 Juillet,jeud_30_06_p6_2019x2020,,,30/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '182,Vendredi 31 Juillet,vend_31_06_m6_2019x2020,,,31/07/2020,GRDS_VACANCES_JUILLET,MINUS6,104,17,4,0',
                '183,Vendredi 31 Juillet,vend_31_06_p6_2019x2020,,,31/07/2020,GRDS_VACANCES_JUILLET,PLUS6,100,20,7,2',
                '184,Lundi 03 Août,lund_03_07_m6_2019x2020,,,03/08/2020,GRDS_VACANCES_AOUT,MINUS6,104,17,4,0',
                '185,Lundi 03 Août,lund_03_07_p6_2019x2020,,,03/08/2020,GRDS_VACANCES_AOUT,PLUS6,100,20,7,2',
                '186,Mardi 04 Août,mard_04_07_m6_2019x2020,,,04/08/2020,GRDS_VACANCES_AOUT,MINUS6,104,17,4,0',
                '187,Mardi 04 Août,mard_04_07_p6_2019x2020,,,04/08/2020,GRDS_VACANCES_AOUT,PLUS6,100,20,7,2',
                '188,Mercredi 05 Août,merc_05_07_m6_2019x2020,,,05/08/2020,GRDS_VACANCES_AOUT,MINUS6,104,17,4,0',
                '189,Mercredi 05 Août,merc_05_07_p6_2019x2020,,,05/08/2020,GRDS_VACANCES_AOUT,PLUS6,100,20,7,2',
                '190,Jeudi 06 Août,jeud_06_07_m6_2019x2020,,,06/08/2020,GRDS_VACANCES_AOUT,MINUS6,104,17,4,0',
                '191,Jeudi 06 Août,jeud_06_07_p6_2019x2020,,,06/08/2020,GRDS_VACANCES_AOUT,PLUS6,100,20,7,2',
                '192,Vendredi 07 Août,vend_07_07_m6_2019x2020,,,07/08/2020,GRDS_VACANCES_AOUT,MINUS6,104,17,4,0',
                '193,Vendredi 07 Août,vend_07_07_p6_2019x2020,,,07/08/2020,GRDS_VACANCES_AOUT,PLUS6,100,20,7,2',
                '194,Lundi 10 Août,lund_10_07_m6_2019x2020,,,10/08/2020,GRDS_VACANCES_AOUT,MINUS6,104,17,4,0',
                '195,Lundi 10 Août,lund_10_07_p6_2019x2020,,,10/08/2020,GRDS_VACANCES_AOUT,PLUS6,100,20,7,2',
                '196,Mardi 11 Août,mard_11_07_m6_2019x2020,,,11/08/2020,GRDS_VACANCES_AOUT,MINUS6,104,17,4,0',
                '197,Mardi 11 Août,mard_11_07_p6_2019x2020,,,11/08/2020,GRDS_VACANCES_AOUT,PLUS6,100,20,7,2',
                '198,Mercredi 12 Août,merc_12_07_m6_2019x2020,,,12/08/2020,GRDS_VACANCES_AOUT,MINUS6,104,17,4,0',
                '199,Mercredi 12 Août,merc_12_07_p6_2019x2020,,,12/08/2020,GRDS_VACANCES_AOUT,PLUS6,100,20,7,2',
                '200,Jeudi 13 Août,jeud_13_07_m6_2019x2020,,,13/08/2020,GRDS_VACANCES_AOUT,MINUS6,104,17,4,0',
                '201,Jeudi 13 Août,jeud_13_07_p6_2019x2020,,,13/08/2020,GRDS_VACANCES_AOUT,PLUS6,100,20,7,2',
                '202,Vendredi 14 Août,vend_14_07_m6_2019x2020,,,14/08/2020,GRDS_VACANCES_AOUT,MINUS6,104,17,4,0',
                '203,Vendredi 14 Août,vend_14_07_p6_2019x2020,,,14/08/2020,GRDS_VACANCES_AOUT,PLUS6,100,20,7,2',
            ]

            raw_json = '{"1":{"id":1,"name":"Septembre","slug":"sept_2019x2020","description":"","date":"","category":"PERI","subcategory":"","order":1,"stock":0,"price":20,"price_q2":0,"price_q1":0},"2":{"id":2,"name":"Octobre","slug":"octo_2019x2020","description":"","date":"","category":"PERI","subcategory":"","order":2,"stock":0,"price":20,"price_q2":0,"price_q1":0},"3":{"id":3,"name":"Novembre","slug":"nove_2019x2020","description":"","date":"","category":"PERI","subcategory":"","order":3,"stock":0,"price":20,"price_q2":0,"price_q1":0},"4":{"id":4,"name":"Décembre","slug":"dece_2019x2020","description":"","date":"","category":"PERI","subcategory":"","order":4,"stock":0,"price":20,"price_q2":0,"price_q1":0},"5":{"id":5,"name":"Janvier","slug":"janv_2019x2020","description":"","date":"","category":"PERI","subcategory":"","order":5,"stock":0,"price":20,"price_q2":0,"price_q1":0},"6":{"id":6,"name":"Février","slug":"fevr_2019x2020","description":"","date":"","category":"PERI","subcategory":"","order":6,"stock":0,"price":20,"price_q2":0,"price_q1":0},"7":{"id":7,"name":"Mars","slug":"mars_2019x2020","description":"","date":"","category":"PERI","subcategory":"","order":7,"stock":0,"price":20,"price_q2":0,"price_q1":0},"8":{"id":8,"name":"Avril","slug":"avri_2019x2020","description":"","date":"","category":"PERI","subcategory":"","order":8,"stock":0,"price":20,"price_q2":0,"price_q1":0},"9":{"id":9,"name":"Mai","slug":"mai_2019x2020","description":"","date":"","category":"PERI","subcategory":"","order":9,"stock":0,"price":20,"price_q2":0,"price_q1":0},"10":{"id":10,"name":"Juin","slug":"juin_2019x2020","description":"","date":"","category":"PERI","subcategory":"","order":10,"stock":0,"price":20,"price_q2":0,"price_q1":0},"11":{"id":11,"name":"Juillet","slug":"juil_2019x2020","description":"","date":"","category":"PERI","subcategory":"","order":11,"stock":0,"price":20,"price_q2":0,"price_q1":0},"12":{"id":12,"name":"Mercredi 04 Septembre","slug":"merc_04_09_m6_2019x2020","description":"","date":"04/09/2019","category":"SEPTEMBRE","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"13":{"id":13,"name":"Mercredi 04 Septembre","slug":"merc_04_09_p6_2019x2020","description":"","date":"04/09/2019","category":"SEPTEMBRE","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"14":{"id":14,"name":"Mercredi 11 Septembre","slug":"merc_11_09_m6_2019x2020","description":"","date":"11/09/2019","category":"SEPTEMBRE","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"15":{"id":15,"name":"Mercredi 11 Septembre","slug":"merc_11_09_p6_2019x2020","description":"","date":"11/09/2019","category":"SEPTEMBRE","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"16":{"id":16,"name":"Mercredi 18 Septembre","slug":"merc_18_09_m6_2019x2020","description":"","date":"18/09/2019","category":"SEPTEMBRE","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"17":{"id":17,"name":"Mercredi 18 Septembre","slug":"merc_18_09_p6_2019x2020","description":"","date":"18/09/2019","category":"SEPTEMBRE","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"18":{"id":18,"name":"Mercredi 25 Septembre","slug":"merc_25_09_m6_2019x2020","description":"","date":"25/09/2019","category":"SEPTEMBRE","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"19":{"id":19,"name":"Mercredi 25 Septembre","slug":"merc_25_09_p6_2019x2020","description":"","date":"25/09/2019","category":"SEPTEMBRE","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"20":{"id":20,"name":"Mercredi 02 Octobre","slug":"merc_02_10_m6_2019x2020","description":"","date":"02/10/2019","category":"OCTOBRE","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"21":{"id":21,"name":"Mercredi 02 Octobre","slug":"merc_02_10_p6_2019x2020","description":"","date":"02/10/2019","category":"OCTOBRE","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"22":{"id":22,"name":"Mercredi 09 Octobre","slug":"merc_09_10_m6_2019x2020","description":"","date":"09/10/2019","category":"OCTOBRE","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"23":{"id":23,"name":"Mercredi 09 Octobre","slug":"merc_09_10_p6_2019x2020","description":"","date":"09/10/2019","category":"OCTOBRE","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"24":{"id":24,"name":"Mercredi 16 Octobre","slug":"merc_16_10_m6_2019x2020","description":"","date":"16/10/2019","category":"OCTOBRE","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"25":{"id":25,"name":"Mercredi 16 Octobre","slug":"merc_16_10_p6_2019x2020","description":"","date":"16/10/2019","category":"OCTOBRE","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"26":{"id":26,"name":"Mercredi 06 Novembre","slug":"merc_06_11_m6_2019x2020","description":"","date":"06/11/2019","category":"NOVEMBRE","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"27":{"id":27,"name":"Mercredi 06 Novembre","slug":"merc_06_11_p6_2019x2020","description":"","date":"06/11/2019","category":"NOVEMBRE","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"28":{"id":28,"name":"Mercredi 13 Novembre","slug":"merc_13_11_m6_2019x2020","description":"","date":"13/11/2019","category":"NOVEMBRE","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"29":{"id":29,"name":"Mercredi 13 Novembre","slug":"merc_13_11_p6_2019x2020","description":"","date":"13/11/2019","category":"NOVEMBRE","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"30":{"id":30,"name":"Mercredi 20 Novembre","slug":"merc_20_11_m6_2019x2020","description":"","date":"20/11/2019","category":"NOVEMBRE","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"31":{"id":31,"name":"Mercredi 20 Novembre","slug":"merc_20_11_p6_2019x2020","description":"","date":"20/11/2019","category":"NOVEMBRE","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"32":{"id":32,"name":"Mercredi 27 Novembre","slug":"merc_27_11_m6_2019x2020","description":"","date":"27/11/2019","category":"NOVEMBRE","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"33":{"id":33,"name":"Mercredi 27 Novembre","slug":"merc_27_11_p6_2019x2020","description":"","date":"27/11/2019","category":"NOVEMBRE","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"34":{"id":34,"name":"Mercredi 04 Décembre","slug":"merc_04_12_m6_2019x2020","description":"","date":"04/12/2019","category":"DECEMBRE","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"35":{"id":35,"name":"Mercredi 04 Décembre","slug":"merc_04_12_p6_2019x2020","description":"","date":"04/12/2019","category":"DECEMBRE","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"36":{"id":36,"name":"Mercredi 11 Décembre","slug":"merc_11_12_m6_2019x2020","description":"","date":"11/12/2019","category":"DECEMBRE","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"37":{"id":37,"name":"Mercredi 11 Décembre","slug":"merc_11_12_p6_2019x2020","description":"","date":"11/12/2019","category":"DECEMBRE","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"38":{"id":38,"name":"Mercredi 18 Décembre","slug":"merc_18_12_m6_2019x2020","description":"","date":"18/12/2019","category":"DECEMBRE","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"39":{"id":39,"name":"Mercredi 18 Décembre","slug":"merc_18_12_p6_2019x2020","description":"","date":"18/12/2019","category":"DECEMBRE","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"40":{"id":40,"name":"Lundi 21 Octobre","slug":"lund_21_10_m6_2019x2020","description":"","date":"21/10/2019","category":"TOUSSAINT","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"41":{"id":41,"name":"Lundi 21 Octobre","slug":"lund_21_10_p6_2019x2020","description":"","date":"21/10/2019","category":"TOUSSAINT","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"42":{"id":42,"name":"Mardi 22 Octobre","slug":"mard_22_10_m6_2019x2020","description":"","date":"22/10/2019","category":"TOUSSAINT","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"43":{"id":43,"name":"Mardi 22 Octobre","slug":"mard_22_10_p6_2019x2020","description":"","date":"22/10/2019","category":"TOUSSAINT","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"44":{"id":44,"name":"Mercredi 23 Octobre","slug":"merc_23_10_m6_2019x2020","description":"","date":"23/10/2019","category":"TOUSSAINT","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"45":{"id":45,"name":"Mercredi 23 Octobre","slug":"merc_23_10_p6_2019x2020","description":"","date":"23/10/2019","category":"TOUSSAINT","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"46":{"id":46,"name":"Jeudi 24 Octobre","slug":"jeud_24_10_m6_2019x2020","description":"","date":"24/10/2019","category":"TOUSSAINT","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"47":{"id":47,"name":"Jeudi 24 Octobre","slug":"jeud_24_10_p6_2019x2020","description":"","date":"24/10/2019","category":"TOUSSAINT","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"48":{"id":48,"name":"Vendredi 25 Octobre","slug":"vend_25_10_m6_2019x2020","description":"","date":"25/10/2019","category":"TOUSSAINT","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"49":{"id":49,"name":"Vendredi 25 Octobre","slug":"vend_25_10_p6_2019x2020","description":"","date":"25/10/2019","category":"TOUSSAINT","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"50":{"id":50,"name":"Lundi 28 Octobre","slug":"lund_28_10_m6_2019x2020","description":"","date":"28/10/2019","category":"TOUSSAINT","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"51":{"id":51,"name":"Lundi 28 Octobre","slug":"lund_28_10_p6_2019x2020","description":"","date":"28/10/2019","category":"TOUSSAINT","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"52":{"id":52,"name":"Mardi 29 Octobre","slug":"mard_29_10_m6_2019x2020","description":"","date":"29/10/2019","category":"TOUSSAINT","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"53":{"id":53,"name":"Mardi 29 Octobre","slug":"mard_29_10_p6_2019x2020","description":"","date":"29/10/2019","category":"TOUSSAINT","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"54":{"id":54,"name":"Mercredi 30 Octobre","slug":"merc_30_10_m6_2019x2020","description":"","date":"30/10/2019","category":"TOUSSAINT","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"55":{"id":55,"name":"Mercredi 30 Octobre","slug":"merc_30_10_p6_2019x2020","description":"","date":"30/10/2019","category":"TOUSSAINT","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"56":{"id":56,"name":"Jeudi 31 Octobre","slug":"jeud_31_10_m6_2019x2020","description":"","date":"31/10/2019","category":"TOUSSAINT","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"57":{"id":57,"name":"Jeudi 31 Octobre","slug":"jeud_31_10_p6_2019x2020","description":"","date":"31/10/2019","category":"TOUSSAINT","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"58":{"id":58,"name":"Lundi 23 Décembre","slug":"lund_23_12_m6_2019x2020","description":"","date":"23/12/2019","category":"NOEL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"59":{"id":59,"name":"Lundi 23 Décembre","slug":"lund_23_12_p6_2019x2020","description":"","date":"23/12/2019","category":"NOEL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"60":{"id":60,"name":"Mardi 24 Décembre","slug":"mard_24_12_m6_2019x2020","description":"","date":"24/12/2019","category":"NOEL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"61":{"id":61,"name":"Mardi 24 Décembre","slug":"mard_24_12_p6_2019x2020","description":"","date":"24/12/2019","category":"NOEL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"62":{"id":62,"name":"Jeudi 26 Décembre","slug":"jeud_26_12_m6_2019x2020","description":"","date":"26/12/2019","category":"NOEL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"63":{"id":63,"name":"Jeudi 26 Décembre","slug":"jeud_26_12_p6_2019x2020","description":"","date":"26/12/2019","category":"NOEL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"64":{"id":64,"name":"Vendredi 27 Décembre","slug":"vend_27_12_m6_2019x2020","description":"","date":"27/12/2019","category":"NOEL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"65":{"id":65,"name":"Vendredi 27 Décembre","slug":"vend_27_12_p6_2019x2020","description":"","date":"27/12/2019","category":"NOEL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"66":{"id":66,"name":"Lundi 30 Décembre","slug":"lund_30_12_m6_2019x2020","description":"","date":"30/12/2019","category":"NOEL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"67":{"id":67,"name":"Lundi 30 Décembre","slug":"lund_30_12_p6_2019x2020","description":"","date":"30/12/2019","category":"NOEL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"68":{"id":68,"name":"Mardi 31 Décembre","slug":"mard_31_12_m6_2019x2020","description":"","date":"31/12/2019","category":"NOEL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"69":{"id":69,"name":"Mardi 31 Décembre","slug":"mard_31_12_p6_2019x2020","description":"","date":"31/12/2019","category":"NOEL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"70":{"id":70,"name":"Jeudi 02 Janvier","slug":"jeud_02_01_m6_2019x2020","description":"","date":"02/01/2020","category":"NOEL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"71":{"id":71,"name":"Jeudi 02 Janvier","slug":"jeud_02_01_p6_2019x2020","description":"","date":"02/01/2020","category":"NOEL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"72":{"id":72,"name":"Vendredi 03 Janvier","slug":"vend_03_01_m6_2019x2020","description":"","date":"03/01/2020","category":"NOEL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"73":{"id":73,"name":"Vendredi 03 Janvier","slug":"vend_03_01_p6_2019x2020","description":"","date":"03/01/2020","category":"NOEL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"74":{"id":74,"name":"Mercredi 08 Janvier","slug":"merc_08_01_m6_2019x2020","description":"","date":"08/01/2020","category":"JANVIER","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"75":{"id":75,"name":"Mercredi 08 Janvier","slug":"merc_08_01_p6_2019x2020","description":"","date":"08/01/2020","category":"JANVIER","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"76":{"id":76,"name":"Mercredi 15 Janvier","slug":"merc_15_01_m6_2019x2020","description":"","date":"15/01/2020","category":"JANVIER","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"77":{"id":77,"name":"Mercredi 15 Janvier","slug":"merc_15_01_p6_2019x2020","description":"","date":"15/01/2020","category":"JANVIER","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"78":{"id":78,"name":"Mercredi 22 Janvier","slug":"merc_22_01_m6_2019x2020","description":"","date":"22/01/2020","category":"JANVIER","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"79":{"id":79,"name":"Mercredi 22 Janvier","slug":"merc_22_01_p6_2019x2020","description":"","date":"22/01/2020","category":"JANVIER","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"80":{"id":80,"name":"Mercredi 29 Janvier","slug":"merc_29_01_m6_2019x2020","description":"","date":"29/01/2020","category":"JANVIER","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"81":{"id":81,"name":"Mercredi 29 Janvier","slug":"merc_29_01_p6_2019x2020","description":"","date":"29/01/2020","category":"JANVIER","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"82":{"id":82,"name":"Mercredi 05 Février","slug":"merc_05_02_m6_2019x2020","description":"","date":"05/02/2020","category":"FEVRIER","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"83":{"id":83,"name":"Mercredi 05 Février","slug":"merc_05_02_p6_2019x2020","description":"","date":"05/02/2020","category":"FEVRIER","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"84":{"id":84,"name":"Mercredi 12 Février","slug":"merc_12_02_m6_2019x2020","description":"","date":"12/02/2020","category":"FEVRIER","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"85":{"id":85,"name":"Mercredi 12 Février","slug":"merc_12_02_p6_2019x2020","description":"","date":"12/02/2020","category":"FEVRIER","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"86":{"id":86,"name":"Mercredi 19 Février","slug":"merc_19_02_m6_2019x2020","description":"","date":"19/02/2020","category":"FEVRIER","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"87":{"id":87,"name":"Mercredi 19 Février","slug":"merc_19_02_p6_2019x2020","description":"","date":"19/02/2020","category":"FEVRIER","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"88":{"id":88,"name":"Mercredi 11 Mars","slug":"merc_11_03_m6_2019x2020","description":"","date":"11/03/2020","category":"MARS","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"89":{"id":89,"name":"Mercredi 11 Mars","slug":"merc_11_03_p6_2019x2020","description":"","date":"11/03/2020","category":"MARS","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"90":{"id":90,"name":"Mercredi 18 Mars","slug":"merc_18_03_m6_2019x2020","description":"","date":"18/03/2020","category":"MARS","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"91":{"id":91,"name":"Mercredi 18 Mars","slug":"merc_18_03_p6_2019x2020","description":"","date":"18/03/2020","category":"MARS","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"92":{"id":92,"name":"Mercredi 25 Mars","slug":"merc_25_03_m6_2019x2020","description":"","date":"25/03/2020","category":"MARS","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"93":{"id":93,"name":"Mercredi 25 Mars","slug":"merc_25_03_p6_2019x2020","description":"","date":"25/03/2020","category":"MARS","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"94":{"id":94,"name":"Mercredi 01 Avril","slug":"merc_01_04_m6_2019x2020","description":"","date":"01/04/2020","category":"AVRIL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"95":{"id":95,"name":"Mercredi 01 Avril","slug":"merc_01_04_p6_2019x2020","description":"","date":"01/04/2020","category":"AVRIL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"96":{"id":96,"name":"Mercredi 22 Avril","slug":"merc_22_04_m6_2019x2020","description":"","date":"22/04/2020","category":"AVRIL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"97":{"id":97,"name":"Mercredi 22 Avril","slug":"merc_22_04_p6_2019x2020","description":"","date":"22/04/2020","category":"AVRIL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"98":{"id":98,"name":"Mercredi 29 Avril","slug":"merc_29_04_m6_2019x2020","description":"","date":"29/04/2020","category":"AVRIL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"99":{"id":99,"name":"Mercredi 29 Avril","slug":"merc_29_04_p6_2019x2020","description":"","date":"29/04/2020","category":"AVRIL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"100":{"id":100,"name":"Mercredi 06 Mai","slug":"merc_06_05_m6_2019x2020","description":"","date":"06/05/2020","category":"MAI","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"101":{"id":101,"name":"Mercredi 06 Mai","slug":"merc_06_05_p6_2019x2020","description":"","date":"06/05/2020","category":"MAI","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"102":{"id":102,"name":"Mercredi 13 Mai","slug":"merc_13_05_m6_2019x2020","description":"","date":"13/05/2020","category":"MAI","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"103":{"id":103,"name":"Mercredi 13 Mai","slug":"merc_13_05_p6_2019x2020","description":"","date":"13/05/2020","category":"MAI","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"104":{"id":104,"name":"Mercredi 20 Mai","slug":"merc_20_05_m6_2019x2020","description":"","date":"20/05/2020","category":"MAI","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"105":{"id":105,"name":"Mercredi 20 Mai","slug":"merc_20_05_p6_2019x2020","description":"","date":"20/05/2020","category":"MAI","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"106":{"id":106,"name":"Mercredi 27 Mai","slug":"merc_27_05_m6_2019x2020","description":"","date":"27/05/2020","category":"MAI","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"107":{"id":107,"name":"Mercredi 27 Mai","slug":"merc_27_05_p6_2019x2020","description":"","date":"27/05/2020","category":"MAI","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"108":{"id":108,"name":"Mercredi 03 Juin","slug":"merc_03_06_m6_2019x2020","description":"","date":"03/06/2020","category":"JUIN","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"109":{"id":109,"name":"Mercredi 03 Juin","slug":"merc_03_06_p6_2019x2020","description":"","date":"03/06/2020","category":"JUIN","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"110":{"id":110,"name":"Mercredi 10 Juin","slug":"merc_10_06_m6_2019x2020","description":"","date":"10/06/2020","category":"JUIN","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"111":{"id":111,"name":"Mercredi 10 Juin","slug":"merc_10_06_p6_2019x2020","description":"","date":"10/06/2020","category":"JUIN","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"112":{"id":112,"name":"Mercredi 17 Juin","slug":"merc_17_06_m6_2019x2020","description":"","date":"17/06/2020","category":"JUIN","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"113":{"id":113,"name":"Mercredi 17 Juin","slug":"merc_17_06_p6_2019x2020","description":"","date":"17/06/2020","category":"JUIN","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"114":{"id":114,"name":"Mercredi 24 Juin","slug":"merc_24_06_m6_2019x2020","description":"","date":"24/06/2020","category":"JUIN","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"115":{"id":115,"name":"Mercredi 24 Juin","slug":"merc_24_06_p6_2019x2020","description":"","date":"24/06/2020","category":"JUIN","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"116":{"id":116,"name":"Mercredi 01 Juillet","slug":"merc_01_07_m6_2019x2020","description":"","date":"01/07/2020","category":"JUILLET","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"117":{"id":117,"name":"Mercredi 01 Juillet","slug":"merc_01_07_p6_2019x2020","description":"","date":"01/07/2020","category":"JUILLET","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"118":{"id":118,"name":"Jeudi 27 Février","slug":"jeud_27_02_m6_2019x2020","description":"","date":"27/02/2020","category":"CARNAVAL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"119":{"id":119,"name":"Jeudi 27 Février","slug":"jeud_27_02_p6_2019x2020","description":"","date":"27/02/2020","category":"CARNAVAL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"120":{"id":120,"name":"Vendredi 28 Février","slug":"vend_28_02_m6_2019x2020","description":"","date":"28/02/2020","category":"CARNAVAL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"121":{"id":121,"name":"Vendredi 28 Février","slug":"vend_28_02_p6_2019x2020","description":"","date":"28/02/2020","category":"CARNAVAL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"122":{"id":122,"name":"Lundi 02 Mars","slug":"lund_02_03_m6_2019x2020","description":"","date":"02/03/2020","category":"CARNAVAL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"123":{"id":123,"name":"Lundi 02 Mars","slug":"lund_02_03_p6_2019x2020","description":"","date":"02/03/2020","category":"CARNAVAL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"124":{"id":124,"name":"Mardi 03 Mars","slug":"mard_03_03_m6_2019x2020","description":"","date":"03/03/2020","category":"CARNAVAL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"125":{"id":125,"name":"Mardi 03 Mars","slug":"mard_03_03_p6_2019x2020","description":"","date":"03/03/2020","category":"CARNAVAL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"126":{"id":126,"name":"Mercredi 04 Mars","slug":"merc_04_03_m6_2019x2020","description":"","date":"04/03/2020","category":"CARNAVAL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"127":{"id":127,"name":"Mercredi 04 Mars","slug":"merc_04_03_p6_2019x2020","description":"","date":"04/03/2020","category":"CARNAVAL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"128":{"id":128,"name":"Jeudi 05 Mars","slug":"jeud_05_03_m6_2019x2020","description":"","date":"05/03/2020","category":"CARNAVAL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"129":{"id":129,"name":"Jeudi 05 Mars","slug":"jeud_05_03_p6_2019x2020","description":"","date":"05/03/2020","category":"CARNAVAL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"130":{"id":130,"name":"Vendredi 06 Mars","slug":"vend_06_03_m6_2019x2020","description":"","date":"06/03/2020","category":"CARNAVAL","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"131":{"id":131,"name":"Vendredi 06 Mars","slug":"vend_06_03_p6_2019x2020","description":"","date":"06/03/2020","category":"CARNAVAL","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"132":{"id":132,"name":"Lundi 06 Avril","slug":"lund_06_04_m6_2019x2020","description":"","date":"06/04/2020","category":"PAQUES","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"133":{"id":133,"name":"Lundi 06 Avril","slug":"lund_06_04_p6_2019x2020","description":"","date":"06/04/2020","category":"PAQUES","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"134":{"id":134,"name":"Mardi 07 Avril","slug":"mard_07_04_m6_2019x2020","description":"","date":"07/04/2020","category":"PAQUES","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"135":{"id":135,"name":"Mardi 07 Avril","slug":"mard_07_04_p6_2019x2020","description":"","date":"07/04/2020","category":"PAQUES","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"136":{"id":136,"name":"Mercre di 08 Avril","slug":"merc_08_04_m6_2019x2020","description":"","date":"08/04/2020","category":"PAQUES","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"137":{"id":137,"name":"Mercredi 08 Avril","slug":"merc_08_04_p6_2019x2020","description":"","date":"08/04/2020","category":"PAQUES","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"138":{"id":138,"name":"Jeudi 09 Avril","slug":"jeud_09_04_m6_2019x2020","description":"","date":"09/04/2020","category":"PAQUES","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"139":{"id":139,"name":"Jeudi 09 Avril","slug":"jeud_09_04_p6_2019x2020","description":"","date":"09/04/2020","category":"PAQUES","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"140":{"id":140,"name":"Mardi 14 Avril","slug":"mard_14_04_m6_2019x2020","description":"","date":"14/04/2020","category":"PAQUES","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"141":{"id":141,"name":"Mardi 14 Avril","slug":"mard_14_04_p6_2019x2020","description":"","date":"14/04/2020","category":"PAQUES","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"142":{"id":142,"name":"Mercredi 15 Avril","slug":"merc_15_04_m6_2019x2020","description":"","date":"15/04/2020","category":"PAQUES","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"143":{"id":143,"name":"Mercredi 15 Avril","slug":"merc_15_04_p6_2019x2020","description":"","date":"15/04/2020","category":"PAQUES","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"144":{"id":144,"name":"Jeudi 16 Avril","slug":"jeud_16_04_m6_2019x2020","description":"","date":"16/04/2020","category":"PAQUES","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"145":{"id":145,"name":"Jeudi 16 Avril","slug":"jeud_16_04_p6_2019x2020","description":"","date":"16/04/2020","category":"PAQUES","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"146":{"id":146,"name":"Vendredi 17 Avril","slug":"vend_17_04_m6_2019x2020","description":"","date":"17/04/2020","category":"PAQUES","subcategory":"MINUS6","order":0,"stock":104,"price":17,"price_q2":4,"price_q1":0},"147":{"id":147,"name":"Vendredi 17 Avril","slug":"vend_17_04_p6_2019x2020","description":"","date":"17/04/2020","category":"PAQUES","subcategory":"PLUS6","order":0,"stock":100,"price":20,"price_q2":7,"price_q1":2},"148":{"id":148,"name":"Lundi 06 Juillet","slug":"lund_06_07_m6_2019x2020","description":"","date":"06/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"149":{"id":149,"name":"Lundi 06 Juillet","slug":"lund_06_07_p6_2019x2020","description":"","date":"06/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"150":{"id":150,"name":"Mardi 07 Juillet","slug":"mard_07_07_m6_2019x2020","description":"","date":"07/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"151":{"id":151,"name":"Mardi 07 Juillet","slug":"mard_07_07_p6_2019x2020","description":"","date":"07/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"152":{"id":152,"name":"Mercredi 08 Juillet","slug":"merc_08_07_m6_2019x2020","description":"","date":"08/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"153":{"id":153,"name":"Mercredi 08 Juillet","slug":"merc_08_07_p6_2019x2020","description":"","date":"08/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"154":{"id":154,"name":"Jeudi 09 Juillet","slug":"jeud_09_07_m6_2019x2020","description":"","date":"09/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"155":{"id":155,"name":"Jeudi 09 Juillet","slug":"jeud_09_07_p6_2019x2020","description":"","date":"09/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"156":{"id":156,"name":"Vendredi 10 Juillet","slug":"vend_10_07_m6_2019x2020","description":"","date":"10/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"157":{"id":157,"name":"Vendredi 10 Juillet","slug":"vend_10_07_p6_2019x2020","description":"","date":"10/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"158":{"id":158,"name":"Lundi 13 Juillet","slug":"lund_13_07_m6_2019x2020","description":"","date":"13/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"159":{"id":159,"name":"Lundi 13 Juillet","slug":"lund_13_07_p6_2019x2020","description":"","date":"13/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"160":{"id":160,"name":"Mercredi 15 Juillet","slug":"merc_15_07_m6_2019x2020","description":"","date":"15/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"161":{"id":161,"name":"Mercredi 15 Juillet","slug":"merc_15_07_p6_2019x2020","description":"","date":"15/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"162":{"id":162,"name":"Jeudi 16 Juillet","slug":"jeud_16_07_m6_2019x2020","description":"","date":"16/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"163":{"id":163,"name":"Jeudi 16 Juillet","slug":"jeud_16_07_p6_2019x2020","description":"","date":"16/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"164":{"id":164,"name":"Vendredi 17 Juillet","slug":"vend_17_07_m6_2019x2020","description":"","date":"17/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"165":{"id":165,"name":"Vendredi 17 Juillet","slug":"vend_17_07_p6_2019x2020","description":"","date":"17/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"166":{"id":166,"name":"Lundi 20 Juillet","slug":"lund_20_07_m6_2019x2020","description":"","date":"20/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"167":{"id":167,"name":"Lundi 20 Juillet","slug":"lund_20_07_p6_2019x2020","description":"","date":"20/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"168":{"id":168,"name":"Mardi 21 Juillet","slug":"mard_21_07_m6_2019x2020","description":"","date":"21/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"169":{"id":169,"name":"Mardi 21 Juillet","slug":"mard_21_07_p6_2019x2020","description":"","date":"21/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"170":{"id":170,"name":"Mercredi 22 Juillet","slug":"merc_22_07_m6_2019x2020","description":"","date":"22/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"171":{"id":171,"name":"Mercredi 22 Juillet","slug":"merc_22_07_p6_2019x2020","description":"","date":"22/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"172":{"id":172,"name":"Jeudi 23 Juillet","slug":"jeud_23_07_m6_2019x2020","description":"","date":"23/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"173":{"id":173,"name":"Jeudi 23 Juillet","slug":"jeud_23_07_p6_2019x2020","description":"","date":"23/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"174":{"id":174,"name":"Vendredi 24 Juillet","slug":"vend_24_07_m6_2019x2020","description":"","date":"24/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"175":{"id":175,"name":"Vendredi 24 Juillet","slug":"vend_24_07_p6_2019x2020","description":"","date":"24/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"176":{"id":176,"name":"Lundi 27 Juillet","slug":"lund_27_07_m6_2019x2020","description":"","date":"27/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"177":{"id":177,"name":"Lundi 27 Juillet","slug":"lund_27_07_p6_2019x2020","description":"","date":"27/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"178":{"id":178,"name":"Mardi 28 Juillet","slug":"mard_28_07_m6_2019x2020","description":"","date":"28/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"179":{"id":179,"name":"Mardi 28 Juillet","slug":"mard_28_07_p6_2019x2020","description":"","date":"28/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"180":{"id":180,"name":"Mercredi 29 Juillet","slug":"merc_29_07_m6_2019x2020","description":"","date":"29/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"181":{"id":181,"name":"Mercredi 29 Juillet","slug":"merc_29_07_p6_2019x2020","description":"","date":"29/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"182":{"id":182,"name":"Jeudi 30 Juillet","slug":"jeud_30_07_m6_2019x2020","description":"","date":"30/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"183":{"id":183,"name":"Jeudi 30 Juillet","slug":"jeud_30_07_p6_2019x2020","description":"","date":"30/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"184":{"id":184,"name":"Vendredi 31 Juillet","slug":"vend_31_07_m6_2019x2020","description":"","date":"31/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"185":{"id":185,"name":"Vendredi 31 Juillet","slug":"vend_31_07_p6_2019x2020","description":"","date":"31/07/2020","category":"GRDS_VACANCES_JUILLET","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"186":{"id":186,"name":"Lundi 03 Août","slug":"lund_03_08_m6_2019x2020","description":"","date":"03/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"187":{"id":187,"name":"Lundi 03 Août","slug":"lund_03_08_p6_2019x2020","description":"","date":"03/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"188":{"id":188,"name":"Mardi 04 Août","slug":"mard_04_08_m6_2019x2020","description":"","date":"04/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"189":{"id":189,"name":"Mardi 04 Août","slug":"mard_04_08_p6_2019x2020","description":"","date":"04/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"190":{"id":190,"name":"Mercredi 05 Août","slug":"merc_05_08_m6_2019x2020","description":"","date":"05/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"191":{"id":191,"name":"Mercredi 05 Août","slug":"merc_05_08_p6_2019x2020","description":"","date":"05/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"192":{"id":192,"name":"Jeudi 06 Août","slug":"jeud_06_08_m6_2019x2020","description":"","date":"06/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"193":{"id":193,"name":"Jeudi 06 Août","slug":"jeud_06_08_p6_2019x2020","description":"","date":"06/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"194":{"id":194,"name":"Vendredi 07 Août","slug":"vend_07_08_m6_2019x2020","description":"","date":"07/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"195":{"id":195,"name":"Vendredi 07 Août","slug":"vend_07_08_p6_2019x2020","description":"","date":"07/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"196":{"id":196,"name":"Lundi 10 Août","slug":"lund_10_08_m6_2019x2020","description":"","date":"10/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"197":{"id":197,"name":"Lundi 10 Août","slug":"lund_10_08_p6_2019x2020","description":"","date":"10/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"198":{"id":198,"name":"Mardi 11 Août","slug":"mard_11_08_m6_2019x2020","description":"","date":"11/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"199":{"id":199,"name":"Mardi 11 Août","slug":"mard_11_08_p6_2019x2020","description":"","date":"11/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"200":{"id":200,"name":"Mercredi 12 Août","slug":"merc_12_08_m6_2019x2020","description":"","date":"12/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"201":{"id":201,"name":"Mercredi 12 Août","slug":"merc_12_08_p6_2019x2020","description":"","date":"12/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"202":{"id":202,"name":"Jeudi 13 Août","slug":"jeud_13_08_m6_2019x2020","description":"","date":"13/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"203":{"id":203,"name":"Jeudi 13 Août","slug":"jeud_13_08_p6_2019x2020","description":"","date":"13/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2},"204":{"id":204,"name":"Vendredi 14 Août","slug":"vend_14_08_m6_2019x2020","description":"","date":"14/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"MINUS6","order":0,"stock":80,"price":17,"price_q2":4,"price_q1":0},"205":{"id":205,"name":"Vendredi 14 Août","slug":"vend_14_08_p6_2019x2020","description":"","date":"14/08/2020","category":"GRDS_VACANCES_AOUT","subcategory":"PLUS6","order":0,"stock":72,"price":20,"price_q2":7,"price_q1":2}}'

            products = json.loads(raw_json)
            print (products['1'])

            categories = {
                '':                         CategoryEnum.UNSET,
                'PERI':                     CategoryEnum.PERI,
                'JANVIER':                  CategoryEnum.JANVIER,
                'FEVRIER':                  CategoryEnum.FEVRIER,
                'MARS':                     CategoryEnum.MARS,
                'AVRIL':                    CategoryEnum.AVRIL,
                'MAI':                      CategoryEnum.MAI,
                'JUIN':                     CategoryEnum.JUIN,
                'JUILLET':                  CategoryEnum.JUILLET,
                'AOUT':                     CategoryEnum.AOUT,
                'SEPTEMBRE':                CategoryEnum.SEPTEMBRE,
                'OCTOBRE':                  CategoryEnum.OCTOBRE,
                'NOVEMBRE':                 CategoryEnum.NOVEMBRE,
                'DECEMBRE':                 CategoryEnum.DECEMBRE,
                'TOUSSAINT':                CategoryEnum.TOUSSAINT,
                'NOEL':                     CategoryEnum.NOEL,
                'CARNAVAL':                 CategoryEnum.CARNAVAL,
                'PAQUES':                   CategoryEnum.PAQUES,
                'GRDS_VACANCES_JUILLET':    CategoryEnum.GRDS_VACANCES_JUILLET,
                'GRDS_VACANCES_AOUT':       CategoryEnum.GRDS_VACANCES_AOUT,
            }

            subcategories = {
                '':    SubCategoryEnum.UNSET,
                'MINUS6':   SubCategoryEnum.MINUS6,
                'PLUS6':    SubCategoryEnum.PLUS6,
            }

            for key in products:
                product = products[key]

                date = datetime.strptime(product['date'], '%d/%m/%Y') if product['date'] else None 

                create_product(
                    product['id'],
                    product['name'],    # name
                    product['slug'],                                 # slug
                    product['description'],                                 # desc
                    product['order'],       # order
                    date,                                                           # date
                    categories[product['category']],                                # category
                    subcategories[product['subcategory']],                          # subcategory

                    0 if product['stock'] == '' else int(product['stock']),         # stock
                    0 if product['price'] == '' else int(product['price']),         # price
                    0 if product['price_q1'] == '' else int(product['price_q1']),   # price Q1
                    0 if product['price_q2'] == '' else int(product['price_q2']),   # price Q2
                    
                    None,
                    None,
                    sy                                      # School Year
                )

            return

            for i, x in enumerate(raw):
                row = x.split(',')

                create_product(
                    i + 1,
                    row[1],                                 # name
                    row[2],                                 # slug
                    row[3],                                 # desc
                    row[4] if row[4] != '' else 0,          # order
                    None if row[5] == '' else datetime.strptime(
                        row[5], '%d/%m/%Y'),  # date
                    categories[row[6]],                     # category
                    subcategories[row[7]],                  # subcategory
                    0 if row[8] == '' else int(row[8]),     # stock
                    0 if row[9] == '' else int(row[9]),     # price
                    0 if row[11] == '' else int(row[11]),   # price Q1
                    0 if row[10] == '' else int(row[10]),   # price Q2
                    None,
                    None,
                    sy                                      # School Year
                )
        
        def create_products_s2(sy):
            raw_json = '''{
                "1":{
                "id":1,
                "name":"Septembre",
                "slug":"sept_2020x2021",
                "description":"",
                "date":"",
                "category":"PERI",
                "subcategory":"",
                "order":1,
                "stock":0,
                "price":20,
                "price_q2":0,
                "price_q1":0
                },
                "2":{
                "id":2,
                "name":"Octobre",
                "slug":"octo_2020x2021",
                "description":"",
                "date":"",
                "category":"PERI",
                "subcategory":"",
                "order":2,
                "stock":0,
                "price":20,
                "price_q2":0,
                "price_q1":0
                },
                "3":{
                "id":3,
                "name":"Novembre",
                "slug":"nove_2020x2021",
                "description":"",
                "date":"",
                "category":"PERI",
                "subcategory":"",
                "order":3,
                "stock":0,
                "price":20,
                "price_q2":0,
                "price_q1":0
                },
                "4":{
                "id":4,
                "name":"Décembre",
                "slug":"dece_2020x2021",
                "description":"",
                "date":"",
                "category":"PERI",
                "subcategory":"",
                "order":4,
                "stock":0,
                "price":20,
                "price_q2":0,
                "price_q1":0
                },
                "5":{
                "id":5,
                "name":"Janvier",
                "slug":"janv_2020x2021",
                "description":"",
                "date":"",
                "category":"PERI",
                "subcategory":"",
                "order":5,
                "stock":0,
                "price":20,
                "price_q2":0,
                "price_q1":0
                },
                "6":{
                "id":6,
                "name":"Février",
                "slug":"fevr_2020x2021",
                "description":"",
                "date":"",
                "category":"PERI",
                "subcategory":"",
                "order":6,
                "stock":0,
                "price":20,
                "price_q2":0,
                "price_q1":0
                },
                "7":{
                "id":7,
                "name":"Mars",
                "slug":"mars_2020x2021",
                "description":"",
                "date":"",
                "category":"PERI",
                "subcategory":"",
                "order":7,
                "stock":0,
                "price":20,
                "price_q2":0,
                "price_q1":0
                },
                "8":{
                "id":8,
                "name":"Avril",
                "slug":"avri_2020x2021",
                "description":"",
                "date":"",
                "category":"PERI",
                "subcategory":"",
                "order":8,
                "stock":0,
                "price":20,
                "price_q2":0,
                "price_q1":0
                },
                "9":{
                "id":9,
                "name":"Mai",
                "slug":"mai_2020x2021",
                "description":"",
                "date":"",
                "category":"PERI",
                "subcategory":"",
                "order":9,
                "stock":0,
                "price":20,
                "price_q2":0,
                "price_q1":0
                },
                "10":{
                "id":10,
                "name":"Juin",
                "slug":"juin_2020x2021",
                "description":"",
                "date":"",
                "category":"PERI",
                "subcategory":"",
                "order":10,
                "stock":0,
                "price":20,
                "price_q2":0,
                "price_q1":0
                },
                "11":{
                "id":11,
                "name":"Juillet",
                "slug":"juil_2020x2021",
                "description":"",
                "date":"",
                "category":"PERI",
                "subcategory":"",
                "order":11,
                "stock":0,
                "price":20,
                "price_q2":0,
                "price_q1":0
                },
                "12":{
                "id":12,
                "name":"Mercredi 02 Septembre",
                "slug":"merc_02_09_m6_2020x2021",
                "description":"",
                "date":"02/09/2019",
                "category":"SEPTEMBRE",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "13":{
                "id":13,
                "name":"Mercredi 02 Septembre",
                "slug":"merc_02_09_p6_2020x2021",
                "description":"",
                "date":"02/09/2019",
                "category":"SEPTEMBRE",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "14":{
                "id":14,
                "name":"Mercredi 09 Septembre",
                "slug":"merc_09_09_m6_2020x2021",
                "description":"",
                "date":"09/09/2019",
                "category":"SEPTEMBRE",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "15":{
                "id":15,
                "name":"Mercredi 09 Septembre",
                "slug":"merc_09_09_p6_2020x2021",
                "description":"",
                "date":"09/09/2019",
                "category":"SEPTEMBRE",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "16":{
                "id":16,
                "name":"Mercredi 16 Septembre",
                "slug":"merc_16_09_m6_2020x2021",
                "description":"",
                "date":"16/09/2019",
                "category":"SEPTEMBRE",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "17":{
                "id":17,
                "name":"Mercredi 16 Septembre",
                "slug":"merc_16_09_p6_2020x2021",
                "description":"",
                "date":"16/09/2019",
                "category":"SEPTEMBRE",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "18":{
                "id":18,
                "name":"Mercredi 23 Septembre",
                "slug":"merc_23_09_m6_2020x2021",
                "description":"",
                "date":"23/09/2019",
                "category":"SEPTEMBRE",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "19":{
                "id":19,
                "name":"Mercredi 23 Septembre",
                "slug":"merc_23_09_p6_2020x2021",
                "description":"",
                "date":"23/09/2019",
                "category":"SEPTEMBRE",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "18_":{
                    "id":18,
                    "name":"Mercredi 30 Septembre",
                    "slug":"merc_30_09_m6_2020x2021",
                    "description":"",
                    "date":"30/09/2019",
                    "category":"SEPTEMBRE",
                    "subcategory":"MINUS6",
                    "order":0,
                    "stock":80,
                    "price":17,
                    "price_q2":4,
                    "price_q1":0
                },
                "19_":{
                    "id":19,
                    "name":"Mercredi 30 Septembre",
                    "slug":"merc_30_09_p6_2020x2021",
                    "description":"",
                    "date":"30/09/2019",
                    "category":"SEPTEMBRE",
                    "subcategory":"PLUS6",
                    "order":0,
                    "stock":72,
                    "price":20,
                    "price_q2":7,
                    "price_q1":2
                },
                "20":{
                "id":20,
                "name":"Mercredi 07 Octobre",
                "slug":"merc_07_10_m6_2020x2021",
                "description":"",
                "date":"07/10/2019",
                "category":"OCTOBRE",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "21":{
                "id":21,
                "name":"Mercredi 07 Octobre",
                "slug":"merc_07_10_p6_2020x2021",
                "description":"",
                "date":"07/10/2019",
                "category":"OCTOBRE",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "22":{
                "id":22,
                "name":"Mercredi 14 Octobre",
                "slug":"merc_14_10_m6_2020x2021",
                "description":"",
                "date":"14/10/2019",
                "category":"OCTOBRE",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "23":{
                "id":23,
                "name":"Mercredi 14 Octobre",
                "slug":"merc_14_10_p6_2020x2021",
                "description":"",
                "date":"14/10/2019",
                "category":"OCTOBRE",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "24":{
                "id":24,
                "name":"Mercredi 21 Octobre",
                "slug":"merc_21_10_m6_2020x2021",
                "description":"",
                "date":"21/10/2019",
                "category":"OCTOBRE",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "25":{
                "id":25,
                "name":"Mercredi 21 Octobre",
                "slug":"merc_21_10_p6_2020x2021",
                "description":"",
                "date":"21/10/2019",
                "category":"OCTOBRE",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "28":{
                "id":28,
                "name":"Mercredi 18 Novembre",
                "slug":"merc_18_11_m6_2020x2021",
                "description":"",
                "date":"18/11/2019",
                "category":"NOVEMBRE",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "29":{
                "id":29,
                "name":"Mercredi 18 Novembre",
                "slug":"merc_18_11_p6_2020x2021",
                "description":"",
                "date":"18/11/2019",
                "category":"NOVEMBRE",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "30":{
                "id":30,
                "name":"Mercredi 25 Novembre",
                "slug":"merc_25_11_m6_2020x2021",
                "description":"",
                "date":"25/11/2019",
                "category":"NOVEMBRE",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "31":{
                "id":31,
                "name":"Mercredi 25 Novembre",
                "slug":"merc_25_11_p6_2020x2021",
                "description":"",
                "date":"25/11/2019",
                "category":"NOVEMBRE",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "34":{
                "id":34,
                "name":"Mercredi 02 Décembre",
                "slug":"merc_02_12_m6_2020x2021",
                "description":"",
                "date":"02/12/2019",
                "category":"DECEMBRE",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "35":{
                "id":35,
                "name":"Mercredi 02 Décembre",
                "slug":"merc_02_12_p6_2020x2021",
                "description":"",
                "date":"02/12/2019",
                "category":"DECEMBRE",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "36":{
                "id":36,
                "name":"Mercredi 09 Décembre",
                "slug":"merc_09_12_m6_2020x2021",
                "description":"",
                "date":"09/12/2019",
                "category":"DECEMBRE",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "37":{
                "id":37,
                "name":"Mercredi 09 Décembre",
                "slug":"merc_09_12_p6_2020x2021",
                "description":"",
                "date":"09/12/2019",
                "category":"DECEMBRE",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "38":{
                "id":38,
                "name":"Mercredi 16 Décembre",
                "slug":"merc_16_12_m6_2020x2021",
                "description":"",
                "date":"16/12/2019",
                "category":"DECEMBRE",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "39":{
                "id":39,
                "name":"Mercredi 16 Décembre",
                "slug":"merc_16_12_p6_2020x2021",
                "description":"",
                "date":"16/12/2019",
                "category":"DECEMBRE",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "40":{
                "id":40,
                "name":"Lundi 26 Octobre",
                "slug":"lund_26_10_m6_2020x2021",
                "description":"",
                "date":"26/10/2019",
                "category":"TOUSSAINT",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "41":{
                "id":41,
                "name":"Lundi 26 Octobre",
                "slug":"lund_26_10_p6_2020x2021",
                "description":"",
                "date":"26/10/2019",
                "category":"TOUSSAINT",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "42":{
                "id":42,
                "name":"Mardi 27 Octobre",
                "slug":"mard_27_10_m6_2020x2021",
                "description":"",
                "date":"27/10/2019",
                "category":"TOUSSAINT",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "43":{
                "id":43,
                "name":"Mardi 27 Octobre",
                "slug":"mard_27_10_p6_2020x2021",
                "description":"",
                "date":"27/10/2019",
                "category":"TOUSSAINT",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "44":{
                "id":44,
                "name":"Mercredi 28 Octobre",
                "slug":"merc_28_10_m6_2020x2021",
                "description":"",
                "date":"28/10/2019",
                "category":"TOUSSAINT",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "45":{
                "id":45,
                "name":"Mercredi 28 Octobre",
                "slug":"merc_28_10_p6_2020x2021",
                "description":"",
                "date":"28/10/2019",
                "category":"TOUSSAINT",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "46":{
                "id":46,
                "name":"Jeudi 29 Octobre",
                "slug":"jeud_29_10_m6_2020x2021",
                "description":"",
                "date":"29/10/2019",
                "category":"TOUSSAINT",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "47":{
                "id":47,
                "name":"Jeudi 29 Octobre",
                "slug":"jeud_29_10_p6_2020x2021",
                "description":"",
                "date":"29/10/2019",
                "category":"TOUSSAINT",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "48":{
                "id":48,
                "name":"Vendredi 30 Octobre",
                "slug":"vend_30_10_m6_2020x2021",
                "description":"",
                "date":"30/10/2019",
                "category":"TOUSSAINT",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "49":{
                "id":49,
                "name":"Vendredi 30 Octobre",
                "slug":"vend_30_10_p6_2020x2021",
                "description":"",
                "date":"30/10/2019",
                "category":"TOUSSAINT",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "50":{
                "id":50,
                "name":"Lundi 02 Novembre",
                "slug":"lund_02_11_m6_2020x2021",
                "description":"",
                "date":"02/11/2019",
                "category":"TOUSSAINT",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "51":{
                "id":51,
                "name":"Lundi 02 Novembre",
                "slug":"lund_02_11_p6_2020x2021",
                "description":"",
                "date":"02/11/2019",
                "category":"TOUSSAINT",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "52":{
                "id":52,
                "name":"Mardi 03 Novembre",
                "slug":"mard_03_10_m6_2020x2021",
                "description":"",
                "date":"03/10/2019",
                "category":"TOUSSAINT",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "53":{
                "id":53,
                "name":"Mardi 03 Novembre",
                "slug":"mard_03_11_p6_2020x2021",
                "description":"",
                "date":"03/11/2019",
                "category":"TOUSSAINT",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "54":{
                "id":54,
                "name":"Mercredi 04 Novembre",
                "slug":"merc_04_11_m6_2020x2021",
                "description":"",
                "date":"04/11/2019",
                "category":"TOUSSAINT",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "55":{
                "id":55,
                "name":"Mercredi 04 Novembre",
                "slug":"merc_04_11_p6_2020x2021",
                "description":"",
                "date":"04/11/2019",
                "category":"TOUSSAINT",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "56":{
                "id":56,
                "name":"Jeudi 05 Novembre",
                "slug":"jeud_05_11_m6_2020x2021",
                "description":"",
                "date":"05/11/2019",
                "category":"TOUSSAINT",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "57":{
                "id":57,
                "name":"Jeudi 05 Novembre",
                "slug":"jeud_05_11_p6_2020x2021",
                "description":"",
                "date":"05/11/2019",
                "category":"TOUSSAINT",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "56_":{
                    "id":56,
                    "name":"Vendredi 06 Novembre",
                    "slug":"vend_06_11_m6_2020x2021",
                    "description":"",
                    "date":"06/11/2019",
                    "category":"TOUSSAINT",
                    "subcategory":"MINUS6",
                    "order":0,
                    "stock":80,
                    "price":17,
                    "price_q2":4,
                    "price_q1":0
                },
                "57_":{
                    "id":57,
                    "name":"Vendredi 06 Novembre",
                    "slug":"vend_06_11_p6_2020x2021",
                    "description":"",
                    "date":"06/11/2019",
                    "category":"TOUSSAINT",
                    "subcategory":"PLUS6",
                    "order":0,
                    "stock":72,
                    "price":20,
                    "price_q2":7,
                    "price_q1":2
                },
                "58":{
                "id":58,
                "name":"Lundi 21 Décembre",
                "slug":"lund_21_12_m6_2020x2021",
                "description":"",
                "date":"21/12/2019",
                "category":"NOEL",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "59":{
                "id":59,
                "name":"Lundi 21 Décembre",
                "slug":"lund_21_12_p6_2020x2021",
                "description":"",
                "date":"21/12/2019",
                "category":"NOEL",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "60":{
                "id":60,
                "name":"Mardi 22 Décembre",
                "slug":"mard_22_12_m6_2020x2021",
                "description":"",
                "date":"22/12/2019",
                "category":"NOEL",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "61":{
                "id":61,
                "name":"Mardi 22 Décembre",
                "slug":"mard_22_12_p6_2020x2021",
                "description":"",
                "date":"22/12/2019",
                "category":"NOEL",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "60_":{
                    "id":60,
                    "name":"Mercrdi 23 Décembre",
                    "slug":"merc_23_12_m6_2020x2021",
                    "description":"",
                    "date":"23/12/2019",
                    "category":"NOEL",
                    "subcategory":"MINUS6",
                    "order":0,
                    "stock":80,
                    "price":17,
                    "price_q2":4,
                    "price_q1":0
                },
                "61_":{
                    "id":61,
                    "name":"Mercrdi 23 Décembre",
                    "slug":"merc_23_12_p6_2020x2021",
                    "description":"",
                    "date":"23/12/2019",
                    "category":"NOEL",
                    "subcategory":"PLUS6",
                    "order":0,
                    "stock":72,
                    "price":20,
                    "price_q2":7,
                    "price_q1":2
                },
                "62":{
                "id":62,
                "name":"Jeudi 24 Décembre",
                "slug":"jeud_24_12_m6_2020x2021",
                "description":"",
                "date":"24/12/2019",
                "category":"NOEL",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "63":{
                "id":63,
                "name":"Jeudi 24 Décembre",
                "slug":"jeud_24_12_p6_2020x2021",
                "description":"",
                "date":"24/12/2019",
                "category":"NOEL",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "66":{
                "id":66,
                "name":"Lundi 28 Décembre",
                "slug":"lund_28_12_m6_2020x2021",
                "description":"",
                "date":"28/12/2019",
                "category":"NOEL",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "67":{
                "id":67,
                "name":"Lundi 28 Décembre",
                "slug":"lund_28_12_p6_2020x2021",
                "description":"",
                "date":"28/12/2019",
                "category":"NOEL",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "68":{
                "id":68,
                "name":"Mardi 29 Décembre",
                "slug":"mard_29_12_m6_2020x2021",
                "description":"",
                "date":"29/12/2019",
                "category":"NOEL",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "69":{
                "id":69,
                "name":"Mardi 29 Décembre",
                "slug":"mard_29_12_p6_2020x2021",
                "description":"",
                "date":"29/12/2019",
                "category":"NOEL",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "70":{
                "id":70,
                "name":"Jeudi 31 Décembre",
                "slug":"jeud_31_01_m6_2020x2021",
                "description":"",
                "date":"31/12/2020",
                "category":"NOEL",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "71":{
                "id":71,
                "name":"Jeudi 02 Décembre",
                "slug":"jeud_02_01_p6_2020x2021",
                "description":"",
                "date":"31/12/2020",
                "category":"NOEL",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "72":{
                "id":72,
                "name":"Vendredi 01 Janvier",
                "slug":"vend_01_01_m6_2020x2021",
                "description":"",
                "date":"01/01/2021",
                "category":"NOEL",
                "subcategory":"MINUS6",
                "order":0,
                "stock":80,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "73":{
                "id":73,
                "name":"Vendredi 01 Janvier",
                "slug":"vend_01_01_p6_2020x2021",
                "description":"",
                "date":"01/01/2021",
                "category":"NOEL",
                "subcategory":"PLUS6",
                "order":0,
                "stock":72,
                "price":20,
                "price_q2":7,
                "price_q1":2
                }
            }'''

            products = json.loads(raw_json)
            print (products['1'])

            categories = {
                '':                         CategoryEnum.UNSET,
                'PERI':                     CategoryEnum.PERI,
                'JANVIER':                  CategoryEnum.JANVIER,
                'FEVRIER':                  CategoryEnum.FEVRIER,
                'MARS':                     CategoryEnum.MARS,
                'AVRIL':                    CategoryEnum.AVRIL,
                'MAI':                      CategoryEnum.MAI,
                'JUIN':                     CategoryEnum.JUIN,
                'JUILLET':                  CategoryEnum.JUILLET,
                'AOUT':                     CategoryEnum.AOUT,
                'SEPTEMBRE':                CategoryEnum.SEPTEMBRE,
                'OCTOBRE':                  CategoryEnum.OCTOBRE,
                'NOVEMBRE':                 CategoryEnum.NOVEMBRE,
                'DECEMBRE':                 CategoryEnum.DECEMBRE,
                'TOUSSAINT':                CategoryEnum.TOUSSAINT,
                'NOEL':                     CategoryEnum.NOEL,
                'CARNAVAL':                 CategoryEnum.CARNAVAL,
                'PAQUES':                   CategoryEnum.PAQUES,
                'GRDS_VACANCES_JUILLET':    CategoryEnum.GRDS_VACANCES_JUILLET,
                'GRDS_VACANCES_AOUT':       CategoryEnum.GRDS_VACANCES_AOUT,
            }

            subcategories = {
                '':    SubCategoryEnum.UNSET,
                'MINUS6':   SubCategoryEnum.MINUS6,
                'PLUS6':    SubCategoryEnum.PLUS6,
            }

            for i, key in enumerate(products):
                product = products[key]

                date = datetime.strptime(product['date'], '%d/%m/%Y') if product['date'] else None 

                create_product(
                    1001 + i,
                    product['name'],    # name
                    product['slug'],                                 # slug
                    product['description'],                                 # desc
                    product['order'],       # order
                    date,                                                           # date
                    categories[product['category']],                                # category
                    subcategories[product['subcategory']],                          # subcategory

                    0 if product['stock'] == '' else int(product['stock']),         # stock
                    0 if product['price'] == '' else int(product['price']),         # price
                    0 if product['price_q1'] == '' else int(product['price_q1']),   # price Q1
                    0 if product['price_q2'] == '' else int(product['price_q2']),   # price Q2
                    
                    None,
                    None,
                    sy                                      # School Year
                )

            return

            for i, x in enumerate(raw):
                row = x.split(',')

                create_product(
                    i + 1,
                    row[1],                                 # name
                    row[2],                                 # slug
                    row[3],                                 # desc
                    row[4] if row[4] != '' else 0,          # order
                    None if row[5] == '' else datetime.strptime(
                        row[5], '%d/%m/%Y'),  # date
                    categories[row[6]],                     # category
                    subcategories[row[7]],                  # subcategory
                    0 if row[8] == '' else int(row[8]),     # stock
                    0 if row[9] == '' else int(row[9]),     # price
                    0 if row[11] == '' else int(row[11]),   # price Q1
                    0 if row[10] == '' else int(row[10]),   # price Q2
                    None,
                    None,
                    sy                                      # School Year
                )

        def core():
            self.s1 = create_school_year(
                datetime(2019, 9, 1),
                datetime(2020, 7, 31)
            )

            s2 = create_school_year(
                datetime(2018, 9, 1),
                datetime(2019, 7, 31)
            )

            self.s3 = create_school_year(
                datetime(2020, 9, 1),
                datetime(2021, 7, 31),
                is_active=True
            )

            create_products_s1(self.s1)
            create_products_s2(self.s3)

        clean()
        core()


    def create_order(self):
        def clean():
            Order.objects.all().delete()
            Ticket.objects.all().delete()
            OrderStatus.objects.all().delete()
            TicketStatus.objects.all().delete()
            OrderMethod.objects.all().delete()

        clean()

        # Bypass last id query
        o = Order.objects.create(
            name='Bypass query order'
        )

        o.status.add(OrderStatus.objects.create(order=o))
        o.methods.add(OrderMethod.objects.create(order=o))

        t = Ticket.objects.create(order=o)
        t.status.add(TicketStatus.objects.create(ticket=t))

        self.client = Client.objects.create(
            id=self.user_parent.id,
            user=self.user_parent.id,
        )

        self.client.credit = ClientCredit.objects.create(
            amount=20.0,
            client=self.client
        )


    def handle(self, *args, **kwargs):
        self.create_params()
        self.create_users()        
        self.create_records()
        self.create_order()


    
