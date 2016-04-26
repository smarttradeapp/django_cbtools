from couchbase import Couchbase
# from couchbase.bucket import Bucket
from couchbase.connection import LOCKMODE_WAIT

from django.conf import settings


def connection():
    if not hasattr(connection, 'singleton'):
        connection.singleton = Couchbase.connect(bucket=settings.COUCHBASE_BUCKET,
                                                 host=settings.COUCHBASE_HOSTS,
                                                 password=settings.COUCHBASE_PASSWORD,
                                                 lockmode=LOCKMODE_WAIT)
    return connection.singleton


# using of Bucket lead to bugs ???
# def connection():
#     if not hasattr(connection, 'singleton'):
#         connection.singleton = Bucket(
#             settings.COUCHBASE_BUCKET,
#             lockmode=LOCKMODE_WAIT,
#             password=settings.COUCHBASE_PASSWORD
#         )
#     return connection.singleton
