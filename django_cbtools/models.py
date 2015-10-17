
from decimal import Decimal
from six import string_types
import logging

from django.db import models
from django.forms.models import model_to_dict
from django.utils import timezone, dateparse
from django.db.models.fields.files import FileField
from django.db.models.fields import DateTimeField, DecimalField
from django.conf import settings

from couchbase.views.iterator import View
from couchbase.views.params import Query, STALE_OK

from tastypie.serializers import Serializer

from django_extensions.db.fields import ShortUUIDField

from django_cbtools import sync_gateway
from django_cbtools.connection import connection

logger = logging.getLogger(__name__)

CHANNELS_FIELD_NAME = "channels"
DOC_TYPE_FIELD_NAME = "doc_type"

CHANNEL_PUBLIC = 'public'


class CouchbaseModelError(Exception):
    pass


class CouchbaseModel(models.Model):
    class Meta:
        abstract = True

    uid_prefix = 'st'
    doc_type = None
    _serializer = Serializer()

    created = models.DateTimeField()
    updated = models.DateTimeField()
    st_deleted = models.BooleanField(default=False)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.get_uid() == other.get_uid()

    def __init__(self, *args, **kwargs):
        self.channels = []
        self.uid = None
        self.rev = None
        if 'uid_prefix' in kwargs:
            self.uid_prefix = kwargs['uid_prefix']
            del kwargs['uid_prefix']

        if 'uid' in kwargs:
            self.uid = kwargs['uid']
            del kwargs['uid']

        if 'rev' in kwargs:
            self.rev = kwargs['rev']
            del kwargs['rev']

        if CHANNELS_FIELD_NAME in kwargs:
            self.channels = kwargs[CHANNELS_FIELD_NAME]
            del kwargs[CHANNELS_FIELD_NAME]

        clean_kwargs = self.__clean_kwargs(kwargs)
        # we never pass args because we never use them
        super(CouchbaseModel, self).__init__(**clean_kwargs)

        if len(args) == 1:
            v = args[0]
            if isinstance(v, string_types):
                self.load(v)

    def append_to_references_list(self, key, value):
        v = getattr(self, key, [])

        if not isinstance(v, list):
            v = []

        if value not in v:
            v.append(value)

        setattr(self, key, v)

    def get_references_list(self, key):
        v = getattr(self, key, [])

        if not isinstance(v, list):
            v = []

        return v

    def delete_from_references_list(self, key, value):
        v = getattr(self, key, [])

        if not isinstance(v, list):
            v = []

        if value in v:
            v.remove(value)

        setattr(self, key, v)

    def is_new(self):
        return not hasattr(self, 'uid') or not self.uid

    def get_uid(self):
        if self.is_new():
            pf = ShortUUIDField()
            self.uid = self.uid_prefix + '_' + pf.create_uuid()
        return self.uid

    def from_json(self, json_payload):
        d = self._serializer.from_json(json_payload)
        self.from_dict(d)

    def from_dict(self, dict_payload):

        for field in self._meta.fields:
            if field.name not in dict_payload:
                continue
            if isinstance(field, DateTimeField):
                self._date_from_string(field.name, dict_payload.get(field.name))
            elif isinstance(field, DecimalField):
                self._decimal_from_string(field.name, dict_payload.get(field.name))
            elif field.name in dict_payload:
                setattr(self, field.name, dict_payload[field.name])

        # converts values into decimal object
        # self._values_to_decimal(dict_payload)
        if CHANNELS_FIELD_NAME in dict_payload.keys():
            self.channels = dict_payload[CHANNELS_FIELD_NAME]

    def _date_from_string(self, field_name, val):
        try:
            setattr(self, field_name, dateparse.parse_datetime(val))
        except Exception as e:
            setattr(self, field_name, val)
            logger.warning('can not parse date (raw value used) %s: %s', field_name, e)

    def _string_from_date(self, field_name):
        try:
            return getattr(self, field_name).isoformat()
        except:
            return None

    def _decimal_from_string(self, field_name, val):
        try:
            setattr(self, field_name, Decimal(val))
        except Exception as e:
            setattr(self, field_name, val)
            logger.warning('can not parse decimal (raw value used) %s: %s', field_name, e)

    def from_dict_nested(self, key, nested_klass, dict_payload):
        setattr(self, key, [])
        nested_list = getattr(self, key)
        if key in dict_payload.keys():
            for d in dict_payload[key]:
                item = nested_klass()
                item.from_dict(d)
                nested_list.append(item)

    def to_dict_nested(self, key, parent_dict):
        parent_dict[key] = []
        for item in getattr(self, key):
            parent_dict[key].append(item.to_dict())
        return parent_dict

    def save(self, *args, **kwargs):
        if not len(self.channels):
            raise CouchbaseModelError('Empty channels list can not be saved')

        self.updated = timezone.now()
        if not hasattr(self, 'created') or self.created is None:
            self.created = self.updated

        # save files
        for field in self._meta.fields:
            # logger.debug(field.name + ' is ' + str(type(field)))
            if isinstance(field, FileField):
                file_field = getattr(self, field.name)

                if not file_field._committed:
                    logger.debug('will save the file to %s' % file_field.name)
                    file_field.save(file_field.name, file_field, False)

        sync_gateway.SyncGateway.save_document(self)

    def load(self, uid):
        d = sync_gateway.SyncGateway.all_docs([uid])
        row = d['rows'][0]
        self.from_sync_gateway_row(row)

    def from_sync_gateway_row(self, row):
        if 'error' in row:
            raise sync_gateway.SyncGatewayException(row)
        self.from_dict(row['doc'])
        self.uid = row['id']
        self.rev = row['value']['rev']
        # self.doc_type = row['doc']['doc_type']

    def to_json(self):
        d = self.to_dict()
        return self._serializer.to_json(d)

    def to_dict(self):
        d = model_to_dict(self)
        tastyjson = self._serializer.to_json(d)
        d = self._serializer.from_json(tastyjson)

        d[DOC_TYPE_FIELD_NAME] = self.get_doc_type()
        d[CHANNELS_FIELD_NAME] = self.channels

        for field in self._meta.fields:
            if isinstance(field, DateTimeField):
                d[field.name] = self._string_from_date(field.name)

        return d

    def get_doc_type(self):
        if self.doc_type:
            return self.doc_type
        return self.__class__.__name__.lower()

    def append_channel(self, channel):
        self.append_to_references_list(CHANNELS_FIELD_NAME, channel)

    def clear_channels(self):
        self.channels = []

    def delete(self):
        """
        This is "soft delete" function. Not real one.
        """
        self.st_deleted = True
        self.save()

    def __unicode__(self):
        return u'%s: %s' % (self.uid, self.to_json())

    def __clean_kwargs(self, data):
        clean_data = {}
        all_names = self._meta.get_all_field_names()
        for fname in data.keys():
            if fname in all_names:
                clean_data[fname] = data[fname]
        return clean_data


class CouchbaseNestedModel(CouchbaseModel):
    class Meta:
        abstract = True

    def to_dict(self):
        d = model_to_dict(self)
        tastyjson = self._serializer.to_json(d)
        d = self._serializer.from_json(tastyjson)
        d['uid'] = self.get_uid()
        return d

    def from_dict(self, dict_payload):
        super(CouchbaseNestedModel, self).from_dict(dict_payload)
        if 'uid' in dict_payload.keys():
            self.uid = dict_payload['uid']

    def save(self, *args, **kwargs):
        raise CouchbaseModelError('this object is not supposed to be saved, it is nested')

    def load(self, uid):
        raise CouchbaseModelError('this object is not supposed to be loaded, it is nested')


def load_objects(keys, class_name):
    """
    Create list of objects of given class_name.
    """
    json = sync_gateway.SyncGateway.all_docs(keys)

    objs = []
    for row in json['rows']:
        obj = class_name()
        obj.from_sync_gateway_row(row)
        objs.append(obj)

    return objs


def load_objects_dict(keys, class_name):
    """
    Creates dictionary (instead of list)
    of obejct of given ``class_name``.
    """
    json = sync_gateway.SyncGateway.all_docs(keys)

    objs = {}
    for row in json['rows']:
        obj = class_name()
        obj.from_sync_gateway_row(row)
        objs[obj.uid] = obj

    return objs


def load_related_objects(objects, related_name, related_class, related_name_suffix='_uid'):
    related_key = related_name + related_name_suffix

    keys = [getattr(x, related_key) for x in objects]

    # we need hash for easier search of related
    # objects by uid
    related_hash = load_objects_dict([x for x in keys if x], related_class)

    for o in objects:
        setattr(o, related_name, related_hash.get(getattr(o, related_key)))


# moved functions
def query_view(view_name, query_key, query=None):
    query = query or Query(key=query_key, stale=get_stale())
    result = View(connection(), settings.COUCHBASE_DESIGN, view_name, query=query)
    result_keys = [x.docid for x in result if 'sync' not in x.docid]
    return result_keys


def query_objects(view_name, query_key, class_name, query=None):
    result = query_view(view_name, query_key=query_key, query=query)
    return load_objects(result, class_name)


def get_stale():
    return settings.COUCHBASE_STALE if hasattr(settings, 'COUCHBASE_STALE') else STALE_OK
