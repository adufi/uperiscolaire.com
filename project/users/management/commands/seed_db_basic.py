import json
from datetime import datetime
from django.core.management.base import BaseCommand

from order.models import Order, OrderMethod, OrderStatus, Ticket, TicketStatus, MethodEnum, StatusEnum
from accounting.models import Client
from users.models import User, UserAuth, Role, UserEmail, UserPhone, UserAddress, UserEmailType
from params.models import Product, ProductStock, SchoolYear, CategoryEnum, SubCategoryEnum
from registration.models import Sibling, SiblingChild, SiblingIntels, Record, Health, ChildPAI, ChildClass, ChildQuotient, RecordAuthorizations, RecordDiseases, RecordRecuperater, RecordResponsible


class Command(BaseCommand):
    help = 'Seed DB with basic data'


    def create_users(self):
        def create_role(name, slug):
            return Role.objects.create(
                name=name,
                slug=slug
            )

        def core():
            r_adm = create_role('Admin', 'admin')
            r_chi = create_role('Child', 'child')
            r_par = create_role('Parent', 'parent')

            self.superuser = User.objects.filter(auth__is_superuser=True).first()
            if self.superuser:
                if not self.superuser.roles.filter(slug='admin'):
                    self.superuser.roles.add(r_adm)

                if not self.superuser.roles.filter(slug='parent'):
                    self.superuser.roles.add(r_par)

                return True

            else:
                print ('No superuser found')
                return False

        return core()


    def create_params(self):
        def create_school_year(date_start, date_end, is_active=False):
            return SchoolYear.objects.create(
                date_start=date_start,
                date_end=date_end,
                is_active=is_active
            )

        def core():
            create_school_year(
                datetime(2020, 9, 1),
                datetime(2021, 8, 31),
                is_active=True
            )

        core()


    def create_records(self):
        def core():
            if not Sibling.objects.filter(parent=self.superuser.id):
                # Create sibling
                Sibling.objects.create(parent=self.superuser.id)

        core()


    def create_order(self):
        # Bypass last id query
        order = Order.objects.create(
            name='Bypass query order'
        )

        order.status.create()
        order.methods.create()

        ticket = order.tickets.create()
        ticket.status.create()

        Client.objects.create_client(id=self.superuser.id)


    def handle(self, *args, **kwargs):
        if self.create_users():        
            self.create_params()
            self.create_records()
            self.create_order()


    
