.. _ref-tutorial:

=====================================
Getting Started with Django Couchbase
=====================================

Django Couchbase is a wrapper around `couchbase <https://pypi.python.org/pypi/couchbase>`_
python library plus several hook to
`sync-gateway <http://developer.couchbase.com/mobile/develop/references/sync-gateway/rest-api/index.html>`_ API.

The document search is perfomred using ``couchbase`` library (directly) connection
to `couchbase server <http://www.couchbase.com/>`_,
but saving and retrieving of the document is done using
`sync-gateway HTTP API <http://developer.couchbase.com/mobile/develop/references/sync-gateway/rest-api/index.html>`_. This is done in order to have documents available for mobile
clients, which can get all benefits of ``couchbase`` library only through ``sync-gateway``.


Configration
============

