import csv

from datetime import datetime
from django.core.management.base import BaseCommand

# from order.models import Order, OrderMethod, OrderStatus, Ticket, TicketStatus, MethodEnum, StatusEnum, Client, ClientCredit
# from users.models import User, UserAuth, Role, UserEmail, UserPhone, UserAddress, UserEmailType
# from params.models import Product, ProductStock, SchoolYear, CategoryEnum, SubCategoryEnum
# from registration.models import Child, Sibling, SiblingChild, Record, CAF, Health, ChildPAI, ChildClass, ChildQuotient

from order.models import Order, OrderMethod, OrderStatus, Ticket, TicketStatus, OrderTypeEnum, MethodEnum, StatusEnum
from users.models import User, Role
from params.models import Product
from registration.models import Sibling, SiblingChild

# from client_intern.utils import OrderHelper

class Command(BaseCommand):
    help = 'Report some products'

    def run(self, filename):

        def get_parent (pk):
            try:
                parent = User.objects.get(pk=pk)
                parent.roles.get(slug='parent')
                return pk
            except User.DoesNotExist:
                raise Exception(f'Le parent ({pk}) n\'existe pas.')
            except Role.DoesNotExist:
                raise Exception('Ce n\'est pas un parent.')

        def get_child (pk):
            try:
                child = User.objects.get(pk=pk)
                child.roles.get(slug='child')
                return pk
            except User.DoesNotExist:
                raise Exception(f'L\'enfant ({pk}) n\'existe pas.')
            except Role.DoesNotExist:
                raise Exception('Ce n\'est pas un enfant.')

        def get_products (raw):
            pks = raw.split(' ')
            res = []
            for pk in pks:
                if not pk:
                    continue
                
                if not Product.objects.filter(pk=pk):
                    raise Exception(f'Le produit ({pk}) n\'existe pas.')
                else:
                    res.append(pk)
            
            return res

        def test_sibling (parent_pk, child_pk):
            try:
                sibling = Sibling.objects.get(parent=parent_pk)
                sibling.children.get(child=child_pk)
            except Sibling.DoesNotExist:
                raise Exception('La famille n\'existe pas.')
            except SiblingChild.DoesNotExist:
                raise Exception('L\'enfant n\'est pas lié.')

        # Parent (0), Enfant 1 (1), Enfant 2 (2), Enfant 3 (3), Enfant 4 (4), Produits (5), Ref (6), Mnt Esp (7), Mnt Chk (8), Ref Chk (9)
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            lcount = 0
            for row in reader:
                # print (row)
                if lcount == 0:
                    titles = []
                    for i, cell in enumerate(row):
                        titles.append(f'{cell} ({i})')
                    print (', '.join(titles))
                else:
                    print (f'Ligne {lcount + 1}')
                    try:
                        parent = get_parent(row[0])

                        # Test children
                        children = []
                        for i in range(1, 5):
                            if not row[i]:
                                continue
                            
                            child = get_child(row[i])
                            # print (f'parent: {parent}, child: {child}')

                            test_sibling(parent, child)
                            children.append(child)

                        # Test products
                        products = get_products(row[5])

                        # Test Methods
                        if not row[7] and not row[8]:
                            raise Exception('Aucune méthode de paiement trouvée.')

                        # Create method
                        mid = OrderMethod.objects.latest('id').id + 1
                        amount = 0
                        method = OrderMethod(id=mid)
                        if row[7]:
                            amount += int(row[7])
                            method.amount = int(row[7])
                            method.method = MethodEnum.CASH

                        elif row[8]:
                            amount += int(row[8])
                            method.amount = int(row[8])
                            method.method = MethodEnum.CHECK
                            method.reference = row[9]

                        # print (f'amount: {method.amount}, ref: {method.reference}, method: {method.method}')

                        # Create order
                        id = Order.objects.latest('id').id + 1
                        order = Order.objects.create(
                            id=id,
                            name='Paiement ALSH/PERI 2020-2021',
                            type=OrderTypeEnum.DIR,
                            reference=row[6],
                            payer=parent,
                            caster=63,
                            amount=amount
                        )
                        order._add_status(StatusEnum.COMPLETED)

                        method.order = order
                        method.save()

                        # print (f'ref: {row[6]}, amount: {amount}')
                        
                        # Create tickets
                        TARIFS_PERI = [20, 16, (40 / 3), 15]
                        PRICE = TARIFS_PERI[len(children) - 1]

                        for child in children:
                            for product in products:
                                tid = Ticket.objects.latest('id').id + 1
                                ticket = Ticket.objects.create(
                                    id=tid,
                                    order=order,
                                    payee=child,
                                    price=PRICE,
                                    product=product
                                )
                                ticket._add_status(StatusEnum.COMPLETED)
                                # print (f'payee: {child}, price: {PRICE}, product: {product}')

                    except Exception as e:
                        print (f'Exception ({e.args[0]})')

                lcount += 1


    def handle(self, *args, **kwargs):
        self.run('project/users/management/commands/payment_GOND_05_01_2021.csv')


    
