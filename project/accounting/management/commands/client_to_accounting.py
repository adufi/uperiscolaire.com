from django.core.management.base import BaseCommand

from order.models import Client as OrderClient, ClientCredit

from accounting.models import Client as AccClient, ClientCreditHistory, HistoryTypeEnum


class Command(BaseCommand):
    help = 'Migrate Order.Client to Accounting.Client'

    def run (self):
        order_clients = OrderClient.objects.all()

        for oc in order_clients:
            try:
                ac = AccClient.objects.get(pk=oc.pk)
                print (f'Object ({oc.id}) found with credits: {oc.credit.amount} <=> {ac.credit}')
            except AccClient.DoesNotExist:
                ac = AccClient.objects.create_client(oc.id)
                ac.set_credit(
                    oc.credit.amount,
                    0, # System
                    HistoryTypeEnum.MIGRATION,
                )

    def handle(self, *args, **kwargs):
        self.run()