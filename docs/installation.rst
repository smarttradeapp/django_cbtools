.. _ref-installation:

============
Installation
============

Settings
--------

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


Requirements
------------

Coming soon...


Testing
-------

You should create a testing couchbase bucket to run the package tests. Certaonly
the bucket you use for your project can be used. And set configuration for that
bucket to a ``settings.py`` file which you use for testing.

The testing bucket must contain ``test`` in the name. Otherwise some
helper functions will raise exception.

Then run tests as usual for django::

    # manage.py test --settings=test_settings django_couchbase
