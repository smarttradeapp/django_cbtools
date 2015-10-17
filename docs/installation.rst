.. _ref-installation:

============
Installation
============

Pre-requisite
-------------

* working Couchbase server / cluster
* working Sync-Gateway server


Requirements
------------

* ``couchbase==2.0.2``
* ``django-extensions==1.5.5``
* ``django-tastypie==0.12.2``
* ``requests==2.7.0``
* ``shortuuid==0.4.2``

``couchbase`` package installation can be tricky. A recipe for Ubuntu 12::

    sudo wget -O/etc/apt/sources.list.d/couchbase.list http://packages.couchbase.com/ubuntu/couchbase-ubuntu1204.list

    wget -O- http://packages.couchbase.com/ubuntu/couchbase.key | sudo apt-key add -

    sudo apt-get update

    sudo apt-get install libcouchbase-dev libcouchbase2-libevent


Quick Install
-------------

Install package::

    pip install git+https://github.com/smarttradeapp/django_couchbase.git

The following configuration settings are used for the package (you can use the set below for the fast installation)::

    COUCHBASE_BUCKET = 'default'
    COUCHBASE_HOSTS = ['127.0.0.1']
    COUCHBASE_PASSWORD = None
    COUCHBASE_DESIGN = 'django_couchbase'
    SYNC_GATEWAY_BUCKET = 'default'
    SYNC_GATEWAY_URL = 'http://127.0.0.1:4984'
    SYNC_GATEWAY_ADMIN_URL = 'http://127.0.0.1:4985'
    SYNC_GATEWAY_USER = "django_couchbase_admin"
    SYNC_GATEWAY_PASSWORD = "django_couchbase_admin_password"
    SYNC_GATEWAY_GUEST_USER = "django_couchbase_guest"
    SYNC_GATEWAY_GUEST_PASSWORD = "django_couchbase_guest_password"

For more detals for settings see :ref:`ref-settings`.

Add ``django_couchbase`` to ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        # ...
        'django_couchbase',
    )

Create folder ``couchbase_views`` in the project root.


Testing
-------

You should create a testing couchbase bucket to run the package tests
(and further your apps tests). For example ``django_couchbase_test``.

The testing bucket must contain ``test`` in the name. Otherwise some
helper functions will raise exception.

Certianly SyncGateway configuration must also have to be configurated properly
to take in account additional bucket, for example::

    {
        "adminInterface":"0.0.0.0:4985",
        "databases": {
            "default": {
                "server": "http://127.0.0.1:8091",
                "bucket": "default"
            },
            "django_couchbase_test": {
                "server": "http://127.0.0.1:8091",
                "bucket": "django_couchbase_test"
            }
        }
    }

Also you need an alternative ``settings.py`` to run tests. Probably you already have
similar file to run your own tests. If you don't it's time to create it now.
The following settings should be changed in order to run Couchbase-related tests properly:

1. ``COUCHBASE_BUCKET`` is targetted to test bucket
2. ``SYNC_GATEWAY_BUCKET`` is targetted to test bucket
3. ``COUCHBASE_STALE`` is set to disable Couchbase caching

Like that, in file ``test_settings.py``::

    # ...
    COUCHBASE_BUCKET = 'django_couchbase_test'
    COUCHBASE_STALE = False
    SYNC_GATEWAY_BUCKET = 'django_couchbase_test'
    # ...

You will have to have at least one view-file in ``couchbase_views`` folder, ``by_channel.js``::

    function (doc, meta) {
        if (doc.st_deleted) {
            return;
        }
        for (channel in doc.channels) {
            emit([doc.channels[channel], doc.doc_type], null)
        }
    }

Now run tests as usual for django::

    python manage.py test --settings=<your-project>.test_settings django_couchbase
