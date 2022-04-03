from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = 'Seed our DB'

    def create_product(self, school_year = 2, name='', desc='', slug='', price=0, category='', subcategory='', stock_cur=0, stock_max=0):
        Product.objects.create(
            name=name,
            desc=desc,
            slug=slug,
            price=price,
            category=category,
            subcategory=subcategory,
            stock_cur=stock_cur,
            stock_max=stock_max,
            school_year=school_year
        )

    def handle(self, *args, **kwargs):       
        # Product.objects.all().delete()

        peri = [
            { 'sub': 'sept', 'slug': 'sept_2019x2020', 'month': 'Septembre',
            { 'sub': 'nove', 'slug': 'nove_2019x2020', 'month': 'Novembre',
            { 'sub': 'octo', 'slug': 'octo_2019x2020', 'month': 'Octobre',
            { 'sub': 'dece', 'slug': 'dece_2019x2020', 'month': 'Décembre',
            { 'sub': 'janv', 'slug': 'janv_2019x2020', 'month': 'Janvier',
            { 'sub': 'Fevr', 'slug': 'fevr_2019x2020', 'month': 'Février',
            { 'sub': 'mars', 'slug': 'mars_2019x2020', 'month': 'Mars',
            { 'sub': 'avri', 'slug': 'avri_2019x2020', 'month': 'Avril',
            { 'sub': 'mai',  'slug': 'mai_2019x2020',  'month': 'Mai',
            { 'sub': 'juin', 'slug': 'juin_2019x2020', 'month': 'Juin'
        ]

        # Peri
        for x in peri:
            self.create_product(
                name=x['month'],    
                slug=x['slug'], 
                desc='Periscolaire',   
                category='peri', 
                subcategory=x['sub'], 
                price=20, 
                school_year=1
            )

        # Alsh
        alsh = [
            {
                'days': ''
            }
        ]
        
        # noel
        self.create_product(
            name='Lundi 01', slug='lund_01_12_m6_2019x2020', desc='ALSH Noel', 
            category='noel', subcategory='moins 6', 
            price=17, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Mardi 02', slug='mard_02_12_m6_2019x2020', desc='ALSH Noel', 
            category='noel', subcategory='moins 6', 
            price=17, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Mercredi 03', slug='merc_03_12_m6_2019x2020', desc='ALSH Noel', 
            category='noel', subcategory='moins 6', 
            price=17, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Jeudi 04', slug='jeud_04_12_m6_2019x2020', desc='ALSH Noel', 
            category='noel', subcategory='moins 6', 
            price=17, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Vendredi 05', slug='vend_05_12_m6_2019x2020', desc='ALSH Noel',
            category='noel', subcategory='moins 6',
            price=17, stock_cur=100, stock_max=100, 
            school_year=2
        )

        self.create_product(
            name='Lundi 01', slug='lund_01_12_p6_2019x2020', desc='ALSH Noel',
            category='noel', subcategory='plus 6',
            price=20, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Mardi 02', slug='mard_02_12_p6_2019x2020', desc='ALSH Noel',
            category='noel', subcategory='plus 6',
            price=20, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Mercredi 03', slug='merc_03_12_p6_2019x2020', desc='ALSH Noel',
            category='noel', subcategory='plus 6',
            price=20, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Jeudi 04', slug='jeud_04_12_p6_2019x2020', desc='ALSH Noel',
            category='noel', subcategory='plus 6',
            price=20, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Vendredi 05', slug='vend_05_12_p6_2019x2020', desc='ALSH Noel',
            category='noel', subcategory='plus 6',
            price=20, stock_cur=100, stock_max=100, 
            school_year=2
        )

        # tous
        self.create_product(
            name='Lundi 01', slug='lund_01_10_m6_2019x2020', desc='ALSH Toussaint',
            category='tous', subcategory='moins 6',
            price=17, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Mardi 02', slug='mard_02_10_m6_2019x2020', desc='ALSH Toussaint',
            category='tous', subcategory='moins 6',
            price=17, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Mercredi 03', slug='merc_03_10_m6_2019x2020', desc='ALSH Toussaint',
            category='tous', subcategory='moins 6',
            price=17, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Jeudi 04', slug='jeud_04_10_m6_2019x2020', desc='ALSH Toussaint',
            category='tous', subcategory='moins 6',
            price=17, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Vendredi 05', slug='vend_05_10_m6_2019x2020', desc='ALSH Toussaint',
            category='tous', subcategory='moins 6',
            price=17, stock_cur=100, stock_max=100, 
            school_year=2
        )

        self.create_product(
            name='Lundi 01', slug='lund_01_10_p6_2019x2020', desc='ALSH Toussaint',
            category='tous', subcategory='plus 6',
            price=20, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Mardi 02', slug='mard_02_10_p6_2019x2020', desc='ALSH Toussaint',
            category='tous', subcategory='plus 6',
            price=20, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Mercredi 03', slug='merc_03_10_p6_2019x2020', desc='ALSH Toussaint',
            category='tous', subcategory='plus 6',
            price=20, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Jeudi 04', slug='jeud_04_10_p6_2019x2020', desc='ALSH Toussaint',
            category='tous', subcategory='plus 6',
            price=20, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Vendredi 05', slug='vend_05_10_p6_2019x2020', desc='ALSH Toussaint',
            category='tous', subcategory='plus 6',
            price=20, stock_cur=100, stock_max=100, 
            school_year=2
        )


        # paques
        self.create_product(
            name='Lundi 01', slug='lund_01_04_m6_2019x2020', desc='ALSH Paques',
            category='paqu', subcategory='moins 6',
            price=17, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Mardi 02', slug='mard_02_04_m6_2019x2020', desc='ALSH Paques',
            category='paqu', subcategory='moins 6',
            price=17, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Mercredi 03', slug='merc_03_04_m6_2019x2020', desc='ALSH Paques',
            category='paqu', subcategory='moins 6',
            price=17, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Jeudi 04', slug='jeud_04_04_m6_2019x2020', desc='ALSH Paques',
            category='paqu', subcategory='moins 6',
            price=17, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Vendredi 05', slug='vend_05_04_m6_2019x2020', desc='ALSH Paques',
            category='paqu', subcategory='moins 6',
            price=17, stock_cur=100, stock_max=100, 
            school_year=2
        )

        self.create_product(
            name='Lundi 01', slug='lund_01_04_p6_2019x2020', desc='ALSH Paques',
            category='paqu', subcategory='plus 6',
            price=20, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Mardi 02', slug='mard_02_04_p6_2019x2020', desc='ALSH Paques',
            category='paqu', subcategory='plus 6',
            price=20, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Mercredi 03', slug='merc_03_04_p6_2019x2020', desc='ALSH Paques',
            category='paqu', subcategory='plus 6',
            price=20, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Jeudi 04', slug='jeud_04_04_p6_2019x2020', desc='ALSH Paques',
            category='paqu', subcategory='plus 6',
            price=20, stock_cur=100, stock_max=100, 
            school_year=2
        )
        self.create_product(
            name='Vendredi 05', slug='vend_05_04_p6_2019x2020', desc='ALSH Paques',
            category='paqu', subcategory='plus 6',
            price=20, stock_cur=100, stock_max=100, 
            school_year=2
        )
