.. _ref-settings:

=========================
Django-Couchbase Settings
=========================

The following configuration settings are used for the package::

    COUCHBASE_BUCKET = 'default'
    COUCHBASE_HOSTS = ['127.0.0.1']
    COUCHBASE_PASSWORD = None
    COUCHBASE_DESIGN = 'django_couchbase'
    COUCHBASE_STALE = False
    SYNC_GATEWAY_BUCKET = 'default'
    SYNC_GATEWAY_URL = 'http://127.0.0.1:4984'
    SYNC_GATEWAY_ADMIN_URL = 'http://127.0.0.1:4985'
    SYNC_GATEWAY_USER = "django_couchbase_admin"
    SYNC_GATEWAY_PASSWORD = "django_couchbase_admin_password"
    SYNC_GATEWAY_GUEST_USER = "django_couchbase_guest"
    SYNC_GATEWAY_GUEST_PASSWORD = "django_couchbase_guest_password"
