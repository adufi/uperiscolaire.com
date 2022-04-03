import json
from datetime import datetime
from django.core.management.base import BaseCommand

from order.models import Order, OrderMethod, OrderStatus, Ticket, TicketStatus, MethodEnum, StatusEnum, Client, ClientCredit
from users.models import User, UserAuth, Role, UserEmail, UserPhone, UserAddress, UserEmailType
from params.models import Product, ProductStock, SchoolYear, CategoryEnum, SubCategoryEnum
from registration.models import Sibling, SiblingChild, SiblingIntels, Record, Health, ChildPAI, ChildClass, ChildQuotient, RecordAuthorizations, RecordDiseases, RecordRecuperater, RecordResponsible


class Command(BaseCommand):
    help = 'Add 2020 products'

    def create_params(self):
        
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


        def create_products_s2(sy):
            raw_json = '''{
                "74":{
                "id":74,
                "name":"Mercredi 06 Janvier",
                "slug":"merc_06_01_m6_2020x2021",
                "description":"",
                "date":"06/01/2021",
                "category":"JANVIER",
                "subcategory":"MINUS6",
                "order":0,
                "stock":100,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "75":{
                "id":75,
                "name":"Mercredi 06 Janvier",
                "slug":"merc_06_01_p6_2020x2021",
                "description":"",
                "date":"06/01/2021",
                "category":"JANVIER",
                "subcategory":"PLUS6",
                "order":0,
                "stock":100,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "76":{
                "id":76,
                "name":"Mercredi 13 Janvier",
                "slug":"merc_13_01_m6_2020x2021",
                "description":"",
                "date":"13/01/2021",
                "category":"JANVIER",
                "subcategory":"MINUS6",
                "order":0,
                "stock":100,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "77":{
                "id":77,
                "name":"Mercredi 13 Janvier",
                "slug":"merc_13_01_p6_2020x2021",
                "description":"",
                "date":"13/01/2021",
                "category":"JANVIER",
                "subcategory":"PLUS6",
                "order":0,
                "stock":100,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "78":{
                "id":78,
                "name":"Mercredi 20 Janvier",
                "slug":"merc_20_01_m6_2020x2021",
                "description":"",
                "date":"20/01/2021",
                "category":"JANVIER",
                "subcategory":"MINUS6",
                "order":0,
                "stock":100,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "79":{
                "id":79,
                "name":"Mercredi 20 Janvier",
                "slug":"merc_20_01_p6_2020x2021",
                "description":"",
                "date":"20/01/2021",
                "category":"JANVIER",
                "subcategory":"PLUS6",
                "order":0,
                "stock":100,
                "price":20,
                "price_q2":7,
                "price_q1":2
                },
                "80":{
                "id":80,
                "name":"Mercredi 27 Janvier",
                "slug":"merc_27_01_m6_2020x2021",
                "description":"",
                "date":"27/01/2021",
                "category":"JANVIER",
                "subcategory":"MINUS6",
                "order":0,
                "stock":100,
                "price":17,
                "price_q2":4,
                "price_q1":0
                },
                "81":{
                "id":81,
                "name":"Mercredi 27 Janvier",
                "slug":"merc_27_01_p6_2020x2021",
                "description":"",
                "date":"27/01/2021",
                "category":"JANVIER",
                "subcategory":"PLUS6",
                "order":0,
                "stock":100,
                "price":20,
                "price_q2":7,
                "price_q1":2
                }
            }'''

            products = json.loads(raw_json)
            # print (products['1'])

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
                id = int(key) + 1000
                product = products[key]

                date = datetime.strptime(product['date'], '%d/%m/%Y') if product['date'] else None 

                create_product(
                    id,
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
            sy = SchoolYear.objects.get(is_active=True)

            create_products_s2(sy)

        core()


    def handle(self, *args, **kwargs):
        self.create_params()


    
