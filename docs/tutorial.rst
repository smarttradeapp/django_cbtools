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


Removing Documents
------------------

The package implements **soft** deletion of the documents. It means
it just set ``st_deleted`` field of the document to ``True``.

A periodic process has to be setup in order to really delete the documents
when you really don't need them.

There are two important points about ``st_deleted`` field:

* ``st_deleted`` field is defined in every document you create within the package.
  You don't have to define it explicitely.
* You should take in account this fields when you create your views.
  Probably you don't want to index the deleted documents.


Couchbase Views
===============

Views in coachbase are JavaScript functions. You can read some more about it
in `couchbase documentation <http://docs.couchbase.com/admin/admin/Views/views-intro.html>`_
as it's out of the scope of this document.

This package goes with two views in: ``by_channel`` (the view which allows you
to find documents by channel name and document type) and ``by_type`` which
can be used to get documents of particular type.

You can see the files of the views in folder ``couchbase_views/`` of the project.
Those files are optional and if you don't need them, just don't copy them to your
project.


Creating Views
--------------

Firstly, create folder ``couchbase_views/`` in your project. Then create
a ``js``-file with your view, for example to find all articles of by the author
``couchbase_views/by_author.js``::

    function (doc, meta) {
        if (doc.st_deleted) {
            // the document is deleted, nothing to index
            return;
        }
        if (doc.doc_type != 'article') {
            // it's not an article document, not for this index
        }
        emit(doc.author_uid, null)
    }

You also may want to create ``reduce`` function for your view. Then create yet another
file with name ``by_author_reduce.js``::

    _count

Now your view has both ``map`` and ``reduce`` parts. The last one is optional.


Deploying Views
---------------

Your couchbase can not be used until they are not in couchbase server. To deploy them
from command line you use command ``deploy_cb_views``::

    # python manage.py deploy_cb_views


Views Helper Functions
----------------------

``get_stale``
~~~~~~~~~~~~~

.. method:: get_stale()

Coming soon...


``query_view``
~~~~~~~~~~~~~~

.. method:: query_view(view_name, query_key, query=None)

Search for ``query_key`` in a view ``view_name``. Return list of
document ``uid`` s. Example::

    import django_couchbase.models import query_view

    uids = query_views('by_author', 'aut_5f8249fef9d1bb2c0a1cf319ae4e8b3d')
    # uids now is list of articles


Internally it builds a quiry for the view, but you can build a generic view
and pass it to perform more complicated view query::

    from couchbase.views.params import Query
    import django_couchbase.models import query_view

    # get all articles of these two authors
    query = Query(
        keys=['aut_8b3d5f8249fef9d1b', 'aut_f8249fef9d1b8b3d5'],
        stale=get_stale()
    )
    uids = query_views(
        'by_author',
        query_key=None,  # will be ignored anyway
        query=query
    )


``query_objects``
~~~~~~~~~~~~~~~~~

.. method:: query_objects(view_name, query_key, class_name, query=None)

Very similar to ``query_view``, but it returns list of object of
given ``class_name`` instead just keys::

    import django_couchbase.models import query_objects
    objects = query_objects('by_author', 'aut_f8249fef9d1b8b3d5', CBAuthor)


Testing
-------

There are several helper functions which you could find useful
in your unit / intergration tests.

Coming soon...

When you write you tests you don't have to deploy the view to test database
every time. Instead you deploy them in ``setUp`` function of your test classes.
