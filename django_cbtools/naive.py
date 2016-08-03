import six

from django_cbtools.connection import connection


def get(uid):
    return CBNaiveModel(uid)


class CBNaiveModel(object):
    related_name_suffix = '_uid'

    def __init__(self, doc=None):
        if isinstance(doc, six.string_types):
            doc = connection().get(doc)

        if doc:
            self.doc = doc.value
            self.uid = doc.key
        else:
            self.doc, self.uid = None, None

    def __getattr__(self, attr):
        if attr in self.doc:
            return self.doc[attr]

        if self._has_related(attr):
            return self._get_related(attr)

        raise AttributeError("Object has no attribute '{}'".format(attr))

    @classmethod
    def load_objects(cls, keys):
        keys = list(keys)

        if not keys:
            return []

        result = connection().get_multi(set(keys))
        return [cls(result[k]) for k in keys]

    @classmethod
    def load_related_objects(cls, objects, related_name):
        related_key = related_name + cls.related_name_suffix

        keys = (getattr(x, related_key) for x in objects)
        unique_keys = set(k for k in keys if k is not None)
        result = connection().get_multi(unique_keys) if unique_keys else {}

        for o in objects:
            doc = result.get(getattr(o, related_key))
            related_obj = CBNaiveModel(doc) if doc else None
            setattr(o, related_name, related_obj)

    def _get_related(self, attr):
        value = self.doc[attr + self.related_name_suffix]
        obj = CBNaiveModel(value) if value else None
        setattr(self, attr, obj)
        return obj

    def _has_related(self, attr):
        try:
            return attr + self.related_name_suffix in self.doc.keys()
        except AttributeError:
            return False

    @classmethod
    def from_dict(cls, *args, **kwargs):
        obj = cls()

        for dictionary in args:
            for key in dictionary:
                setattr(obj, key, dictionary[key])

        for key in kwargs:
            setattr(obj, key, kwargs[key])

        return obj
