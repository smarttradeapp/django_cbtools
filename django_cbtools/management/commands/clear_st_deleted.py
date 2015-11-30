from datetime import timedelta

from couchbase.views.params import Query

from django_cbtools.models import get_stale, CouchbaseModel, query_view
from django_cbtools.sync_gateway import SyncGateway

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    def handle(self, *args, **options):
        latest_modification_time = timezone.now() - timedelta(days=30)
        date_to = latest_modification_time.date().isoformat()

        for uid in self.get_uids(date_to):
            o = CouchbaseModel(uid)
            # print 'will delete %s / %s' % (uid, o.rev)
            SyncGateway.delete_document(uid, o.rev)

    def get_uids(self, date_string):
        query = Query(endkey=date_string, stale=get_stale())
        return query_view('deleted_documents', None, query=query)
