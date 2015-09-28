================
Django Couchbase
================

Django Couchbase is a wrapper around `couchbase <https://pypi.python.org/pypi/couchbase>`_
python library plus several hook to
`Sync-Gateway <http://developer.couchbase.com/mobile/develop/references/sync-gateway/rest-api/index.html>`_ API.

The document search is perfomred using ``couchbase`` library (directly) connection
to `couchbase server <http://www.couchbase.com/>`_,
but saving and retrieving of the document is done using
`Sync-Gateway HTTP API <http://developer.couchbase.com/mobile/develop/references/sync-gateway/rest-api/index.html>`_. This is done in order to have documents available for mobile
clients, which can get all benefits of ``couchbase`` library only through Sync-Gateway.

The essential part of the package is models. They are inherited from django models
with almost all the benefits they have: can be validated with django forms and have fields
all sort of field you are used to have.

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
    COUCHBASE_STALE = False
    SYNC_GATEWAY_BUCKET = 'default'
    SYNC_GATEWAY_URL = 'http://127.0.0.1:4984'
    SYNC_GATEWAY_ADMIN_URL = 'http://127.0.0.1:4985'
    SYNC_GATEWAY_USER = "django_couchbase_admin"
    SYNC_GATEWAY_PASSWORD = "django_couchbase_admin_password"
    SYNC_GATEWAY_GUEST_USER = "django_couchbase_guest"
    SYNC_GATEWAY_GUEST_PASSWORD = "django_couchbase_guest_password"

For more detals for settings see `settings <http://django-couchbase.readthedocs.org/en/latest/settings.html>`_.


Testing
-------

You should create a testing couchbase bucket to run the package tests. Certaonly
the bucket you use for your project can be used. And set configuration for that
bucket to a ``settings.py`` file which you use for testing.

The testing bucket must contain ``test`` in the name. Otherwise some
helper functions will raise exception.

Then run tests as usual for django::

    # manage.py test --settings=test_settings django_couchbase
