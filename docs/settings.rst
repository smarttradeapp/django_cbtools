.. _ref-settings:

=======================
Django-Cbtools Settings
=======================

Full list of setting Django-Cbtools recognizes.

.. warning::

    Please don't use username and password from the lines below!


``COUCHBASE_BUCKET``
====================

An example::

    COUCHBASE_BUCKET = 'default'

``COUCHBASE_HOSTS``
===================

Couchbase server hosts.

An example::

    COUCHBASE_HOSTS = ['127.0.0.1']


``COUCHBASE_PASSWORD``
======================

Couchbase password.

An example::

    COUCHBASE_PASSWORD = None

OR::

    COUCHBASE_PASSWORD = 'password'


``COUCHBASE_DESIGN``
====================

A name of design document where couchbase will store the views.

An example::

    COUCHBASE_DESIGN = 'design_doc_name'


``COUCHBASE_STALE``
===================

Caching option for views. It's used as a query parameter.
Read about values in `couchbase  documentation <http://docs.couchbase.com/admin/admin/Views/views-operation.html>`_.

An example::

    COUCHBASE_STALE = False

OR::

    from couchbase.views.params import STALE_OK
    COUCHBASE_STALE = STALE_OK


``SYNC_GATEWAY_BUCKET``
=======================

Basicly it's probably the same as ``COUCHBASE_BUCKET``.
But Sync-Gateway can have different settings.

An example::

    SYNC_GATEWAY_BUCKET = 'default'


``SYNC_GATEWAY_URL``
====================

An URL for Sync-Gateway server.

An example::

    SYNC_GATEWAY_URL = 'http://127.0.0.1:4984'


``SYNC_GATEWAY_ADMIN_URL``
==========================

It's probably the same as ``SYNC_GATEWAY_URL`` but with different port number.

An example::

    SYNC_GATEWAY_ADMIN_URL = 'http://127.0.0.1:4985'


``SYNC_GATEWAY_USER``
=====================

The user which will be used to access the couchbase by your application.

An example::

    SYNC_GATEWAY_USER = "admin"


``SYNC_GATEWAY_PASSWORD``
=========================

Password for the user above.

An example::

    SYNC_GATEWAY_PASSWORD = "admin_password"


``SYNC_GATEWAY_GUEST_USER``
===========================

Guest user.

An example::

    SYNC_GATEWAY_GUEST_USER = "guest"


``SYNC_GATEWAY_GUEST_PASSWORD``
===============================

Password for the user above.

An example::

    SYNC_GATEWAY_GUEST_PASSWORD = "guest_password"
