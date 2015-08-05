from couchbase import Couchbase
from couchbase.connection import *

from django.conf import settings

__COUCHBASE_CONNECTION__ = None


def connection(reconnect=False):

    global __COUCHBASE_CONNECTION__

    if reconnect:
        __COUCHBASE_CONNECTION__ = None

    if __COUCHBASE_CONNECTION__ is None:
        __COUCHBASE_CONNECTION__ = Couchbase.connect(bucket=settings.COUCHBASE_BUCKET,
                                                     host=settings.COUCHBASE_HOSTS,
                                                     password=settings.COUCHBASE_PASSWORD,
                                                     lockmode=LOCKMODE_WAIT)

    return __COUCHBASE_CONNECTION__
