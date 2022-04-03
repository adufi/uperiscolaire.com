import json
from datetime import datetime
from django.core.management.base import BaseCommand

from order.models import Order, OrderMethod, OrderStatus, Ticket, TicketStatus, MethodEnum, StatusEnum, Client, ClientCredit
from users.models import User, UserAuth, Role, UserEmail, UserPhone, UserAddress, UserEmailType
from params.models import Product, ProductStock, SchoolYear, CategoryEnum, SubCategoryEnum
from registration.models import Sibling, SiblingChild, SiblingIntels, Record, Health, ChildPAI, ChildClass, ChildQuotient, RecordAuthorizations, RecordDiseases, RecordRecuperater, RecordResponsible


class Command(BaseCommand):
    help = 'Add 2021 products for FdF'

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
                "date":"02/09/2020",
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
                "date":"02/09/2020",
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
                "date":"09/09/2020",
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
                "date":"09/09/2020",
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
                "date":"16/09/2020",
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
                "date":"16/09/2020",
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
                "date":"23/09/2020",
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
                "date":"23/09/2020",
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
                    "date":"30/09/2020",
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
                    "date":"30/09/2020",
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
                "date":"07/10/2020",
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
                "date":"07/10/2020",
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
                "date":"14/10/2020",
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
                "date":"14/10/2020",
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
                "date":"21/10/2020",
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
                "date":"21/10/2020",
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
                "date":"18/11/2020",
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
                "date":"18/11/2020",
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
                "date":"25/11/2020",
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
                "date":"25/11/2020",
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
                "date":"02/12/2020",
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
                "date":"02/12/2020",
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
                "date":"09/12/2020",
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
                "date":"09/12/2020",
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
                "date":"16/12/2020",
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
                "date":"16/12/2020",
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
                "date":"26/10/2020",
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
                "date":"26/10/2020",
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
                "date":"27/10/2020",
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
                "date":"27/10/2020",
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
                "date":"28/10/2020",
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
                "date":"28/10/2020",
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
                "date":"29/10/2020",
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
                "date":"29/10/2020",
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
                "date":"30/10/2020",
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
                "date":"30/10/2020",
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
                "date":"02/11/2020",
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
                "date":"02/11/2020",
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
                "date":"03/10/2020",
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
                "date":"03/11/2020",
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
                "date":"04/11/2020",
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
                "date":"04/11/2020",
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
                "date":"05/11/2020",
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
                "date":"05/11/2020",
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
                    "date":"06/11/2020",
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
                    "date":"06/11/2020",
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
                "date":"21/12/2020",
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
                "date":"21/12/2020",
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
                "date":"22/12/2020",
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
                "date":"22/12/2020",
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
                    "date":"23/12/2020",
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
                    "date":"23/12/2020",
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
                "date":"24/12/2020",
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
                "date":"24/12/2020",
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
                "date":"28/12/2020",
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
                "date":"28/12/2020",
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
                "date":"29/12/2020",
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
                "date":"29/12/2020",
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
            sy = SchoolYear.objects.get(is_active=True)

            create_products_s2(sy)

        core()


    def handle(self, *args, **kwargs):
        self.create_params()


    
