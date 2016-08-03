from django.core.paginator import Paginator, Page

from django_cbtools import models, naive


class CouchbasePaginator(Paginator):
    def __init__(self, *args, **kwargs):
        assert 'model' in kwargs
        assert issubclass(kwargs['model'], models.CouchbaseModel)

        self.model = kwargs['model']
        del kwargs['model']

        if 'naive' in kwargs:
            self.naive = naive
            del kwargs['naive']
        else:
            self.naive = False

        super(CouchbasePaginator, self).__init__(*args, **kwargs)

    def _get_page(self, *args, **kwargs):
        return CouchbasePage(*args, **kwargs)


class CouchbasePage(Page):
    def __init__(self, object_list, number, paginator):
        assert isinstance(paginator, CouchbasePaginator)

        if paginator.naive:
            obj_list = naive.CBNaiveModel.load_objects(object_list)
            obj_list = [paginator.model.from_naive(o) for o in obj_list]
        else:
            obj_list = models.load_objects(object_list, paginator.model)

        super(CouchbasePage, self).__init__(obj_list, number, paginator)
