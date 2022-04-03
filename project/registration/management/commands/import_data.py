from django.core.management.base import BaseCommand

from registration.models import Family


class Command(BaseCommand):
    help = 'Import and update child '

    def create_family(self, parent=0, child=0):
        if parent != 0 and child != 0:
            Family.objects.create(parent=parent, child=child)

    def handle(self, *args, **kwargs):
        self.create_family(17, 20)
        self.create_family(17, 21)
        self.create_family(17, 22)

        self.create_family(18, 23)
        self.create_family(18, 24)
        self.create_family(18, 25)

        self.create_family(19, 26)
        self.create_family(19, 27)
        self.create_family(19, 28)
