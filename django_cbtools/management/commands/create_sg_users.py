from django.core.management.base import BaseCommand

from django_cbtools.sync_gateway import SyncGateway


class Command(BaseCommand):

    def handle(self, *args, **options):
        SyncGateway.put_admin_user()
        SyncGateway.put_guest_user()
