from django.core.management.base import BaseCommand

from users.models import User
from accounting.models import Client, ClientCreditHistory, HistoryTypeEnum


class Command(BaseCommand):
    help = 'Migrate Order.Client to Accounting.Client'

    def run (self):
        users = User.objects.all()

        for user in users:
            try:
                client = Client.objects.get(pk=user.pk)
                # print (f'Object ({oc.id}) found with credits: {oc.credit.amount} <=> {client.credit}')
            except Client.DoesNotExist:
                client = Client.objects.create_client(user.id)

    def handle(self, *args, **kwargs):
        self.run()