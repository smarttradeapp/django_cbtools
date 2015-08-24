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


Creating Model
==============

Typical couchbase model class looks like that::

    from django_couchnase.models import CouchbaseModel

    class CBArticle(CouchbaseModel):
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


Getting Documents
-----------------

The document creation is a stright forward process::

    article = CBArticle()
    article.title = 'You & Couchbase'

Or alternatively::

    article = CBArticle(title='You & Couchbase')


Saving Documents / Channels
---------------------------

Ideally it should be as simple as that::

    article = CBArticle(title='Couchbase & You')
    article.save()

But if you do that you get exception::

    CouchbaseModelError: Empty channels list can not be saved

Channels. This is how ``sync-gateway`` limit access to the documents
for different mobile clients. The server side
framework uses an admin user to create and save documents, so it has
access to all of them, but we mind mobile clients also. So::

    article = CBArticle(title='Couchbase & You', channels=['channel_name'])
    article.save()

or::

    article = CBArticle(title='Couchbase & You')
    article.append_channel('channel_name')
    article.save()

``channel_name`` is given here as an example. In real world it will
probably somehow related to your users. For example, somewhere in a view::

    article = CBArticle(title='Couchbase & You')
    article.append_channel(self.request.user.username)
    article.save()

You can / should read some more about the concept of channels for
``sync-gateway`` `here <http://developer.couchbase.com/mobile/develop/guides/sync-gateway/channels/index.html>`_.


Load Documents
--------------

You usually load document if you have its ``UID``::

    article = CBArticle('atl_0a1cf319ae4e8b3d5f8249fef9d1bb2c')
    print article


Load Related Documents
----------------------

This is how the model supports relations. Just a small helper method to load
related object. In our example above it's an ``author`` document::

    from django_couchbase.model import load_related_objects

    article = CBArticle('atl_0a1cf319ae4e8b3d5f8249fef9d1bb2c')
    load_related_objects([article], 'author', CBAuthor)
    print article.author

The function above just create another instance variable ``author`` with  loaded
``CBAuthor`` document. By default it will check for ``UID`` in a filed with name
``author_uid``.

Please note, the function will make only one request to couchbase to load all
the related documents for the given documents.


Couchbase Views
===============

Views in coachbase are JavaScript functions. You can read some more about it
`here <http://docs.couchbase.com/admin/admin/Views/views-intro.html>`_
as it's out of the scope of this document. Please do read the docs by the link,
they are quite good.

This package goes with two views: ``by_channel`` (the view which allows you
to find documents by channel name and document type) and ``by_type`` which
can be used to get documents of particular type.

You can see the files of the views in folder ``couchbase_views/`` of the project.
Those files are optional and if you don't need them, just don't copy them to your
project.


Creating Views
--------------

Coming soon...


Deploying Views
---------------

Coming soon...


Index Helper Functions
----------------------

Coming soon...

