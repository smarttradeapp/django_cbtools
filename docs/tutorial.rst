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

The essential part of the package is models. They are inherited from django models
with almost all the benefits they have: can be validated with django forms and have fields
all sort of field you are used to have.

Typical couchbase model class looks like that::

    class CBArticle (CouchbaseModel):
        class Meta:
            abstract = True

        doc_type = 'article'
        uid_prefix = 'atl'

        title = models.CharField(max_length=45, null=True, blank=True)
        year_published = models.IntegerField(default=2014)
        is_draft = models.BooleanField(default=True)

        author_uid = models.TextField()

Certainly you can use all the rest types of fields. Let's review the code above.

* The class has a prefix ``CB``. It is optional. But you will probably have models
  related to your relational database. So to distinguish them we find it's useful
  to have this small prefix.
* ``abstract = True`` this is to avoud django migration tool to take care about
  changes in the couchbase models.
* ``doc_type = 'article'`` is the field you have to define. This is the way
  django_couchbase stores the type of the objects. This value is stored in the
  database.
* ``uid_prefix = 'atl'`` this is an optional prefix for the ``uid`` of the document.
  Having prefix for the ``uid`` help a lot to debug the application. For example you
  can easily define type of the document having just its ``uid``. Very useful.


Configuration
=============

