import json
from decimal import Decimal
from datetime import datetime

from django.test import TestCase
from django.db import models
from django.conf import settings
from django.utils import timezone

from django_cbtools import models as cbm
from django_cbtools.models import query_objects, load_related_objects
from django_cbtools.sync_gateway import SyncGateway, SyncGatewayException


class Transaction(cbm.CouchbaseModel):
    class Meta:
        abstract = True
    doc_type = 'trn'

    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


class Money(cbm.CouchbaseModel):
    class Meta:
        abstract = True
    doc_type = 'tst'

    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


class Stamp(cbm.CouchbaseModel):
    class Meta:
        abstract = True
    doc_type = 'tst'

    stamp = models.DateTimeField(null=True)


class Mock(cbm.CouchbaseModel):
    class Meta:
        abstract = True
    doc_type = 'mock'

    title = models.CharField(max_length=255)
    title2 = models.CharField(max_length=255)
    num = models.IntegerField()
    b = models.BooleanField()


class Mock2(Mock):
    class Meta:
        abstract = True

    doc_type = 'qwe'


class Job(cbm.CouchbaseModel):
    class Meta:
        abstract = True

    uid_prefix = 'job'
    title = models.CharField(max_length=255)

    def to_dict(self):
        d = super(Job, self).to_dict()
        self.to_dict_nested('payments', d)
        return d

    def from_dict(self, dict_payload):
        super(Job, self).from_dict(dict_payload)
        self.from_dict_nested('payments', Payment, dict_payload)


def clean_buckets():
    if 'test' not in settings.COUCHBASE_BUCKET:
        raise Exception('will not clean non-test bucket')

    all_docs = SyncGateway.all_docs([], really_all=True)

    for i in all_docs['rows']:
        uid = i['id']
        rev = i['value']['rev']
        if 'sync' in uid:
            continue
        # print 'del %s' % uid
        SyncGateway.delete_document(uid, rev)


class Payment(cbm.CouchbaseNestedModel):
    class Meta:
        abstract = True

    uid_prefix = 'pmt'
    amount = models.DecimalField(max_digits=5, decimal_places=2)


class CouchbaseModelTestCase(TestCase):
    def setUp(self):
        SyncGateway.put_admin_user()
        clean_buckets()

    def tearDown(self):
        pass

    def test_eq(self):
        m1 = Mock()
        m1.append_channel('foo')
        m2 = Mock()
        m2.append_channel('bar')
        self.assertNotEqual(m1, m2)

        m3 = Mock()
        m3.uid = m1.uid
        self.assertEqual(m1, m3)

        m1.save()
        m2.save()

        m1_loaded = Mock(m1.uid)
        m2_loaded = Mock(m2.uid)

        self.assertEqual(m1, m1_loaded)
        self.assertEqual(m2, m2_loaded)
        self.assertNotEqual(m1_loaded, m2_loaded)

    def test_created_updated(self):
        now = timezone.now().isoformat()

        m = Mock()
        m.append_channel('foo')
        m.save()

        m = Mock(m.uid)
        self.assertTrue(hasattr(m, 'created'))
        self.assertTrue(hasattr(m, 'updated'))
        self.assertTrue(now <= m.created.isoformat())
        self.assertTrue(now <= m.updated.isoformat())

        # created must be set even after get_uid call
        m = Mock()
        m.get_uid()
        m.append_channel('foo')
        m.save()
        m = Mock(m.uid)
        self.assertTrue(hasattr(m, 'created'))
        self.assertTrue(hasattr(m, 'updated'))

        self.assertTrue(now <= m.created.isoformat())
        self.assertTrue(now <= m.updated.isoformat())

    def test_st_deleted_new_object(self):
        uid = 'some_key'
        data = dict(title2='title')
        SyncGateway.save_json(uid, data)
        m = Mock(uid)
        self.assertFalse(m.st_deleted)

    def test_st_deleted_old_loaded(self):
        m = Mock()
        self.assertFalse(m.st_deleted)

    def test_st_deleted_loaded(self):
        m = Mock()
        m.append_channel('foo')
        m.save()
        m = Mock(m.uid)
        self.assertFalse(m.st_deleted)

    def test_st_deleted(self):
        m = Mock()
        m.append_channel('foo')
        m.save()
        m = Mock(m.uid)
        self.assertFalse(m.st_deleted)

        m.delete()
        self.assertTrue(m.st_deleted)

        m = Mock(m.uid)
        self.assertTrue(m.st_deleted)

    def test_append_to_references_list(self):
        m = Mock()
        m.append_to_references_list('some_key', 'some_value')
        self.assertEqual(m.some_key, ['some_value'])
        m.append_to_references_list('some_key', 'some_value')
        self.assertEqual(m.some_key, ['some_value'])
        m.append_to_references_list('some_key', 'some_value2')
        self.assertEqual(m.some_key, ['some_value', 'some_value2'])

        m.some_key2 = ''
        m.append_to_references_list('some_key2', 'some_value')
        self.assertEqual(m.some_key2, ['some_value'])
        m.append_to_references_list('some_key2', 'some_value')
        self.assertEqual(m.some_key2, ['some_value'])
        m.append_to_references_list('some_key2', 'some_value2')
        self.assertEqual(m.some_key2, ['some_value', 'some_value2'])

    def test_get_references_list(self):
        m = Mock()
        v = m.get_references_list('some_key')
        self.assertEqual(v, [])

        m = Mock()
        m.some_key = ''
        v = m.get_references_list('some_key')
        self.assertEqual(v, [])

        m = Mock()
        m.some_key = ['some_value']
        v = m.get_references_list('some_key')
        self.assertEqual(v, ['some_value'])

    def test_delete_from_refernces_list(self):
        m = Mock()
        m.delete_from_references_list('some_key', 'some_value')
        self.assertEqual(m.some_key, [])

        m = Mock()
        m.some_key = ''
        m.delete_from_references_list('some_key', 'some_value')
        self.assertEqual(m.some_key, [])

        m = Mock()
        m.some_key = []
        m.delete_from_references_list('some_key', 'some_value')
        self.assertEqual(m.some_key, [])

        m = Mock()
        m.some_key = ['some_value', 'some_value2']
        m.delete_from_references_list('some_key', 'some_value')
        self.assertEqual(m.some_key, ['some_value2'])
        m.delete_from_references_list('some_key', 'some_value')
        self.assertEqual(m.some_key, ['some_value2'])

    def test_init(self):
        m = Mock(title="my title", b=True)
        m.num = 12

        self.assertEqual(m.title, "my title")
        self.assertEqual(m.num, 12)
        self.assertTrue(m.b)
        self.assertIsNone(m.uid)

    def test_bug_with_load_by_uid(self):
        # it sets uid value to first textfield
        uid = 'unfilled_model_uid'
        incomplete_data = dict(title2='title')
        SyncGateway.save_json(uid, incomplete_data)
        m = Mock(uid)
        self.assertNotEqual(uid, m.title)
        self.assertFalse(bool(m.title))

    def test_init_with_wrong_fields(self):
        try:
            m = Mock(title="my title", b=True, foo='bar')
        except Exception as e:
            self.fail('failed: %s' % e)

        m.num = 12

        self.assertEqual(m.title, "my title")
        self.assertEqual(m.num, 12)
        self.assertTrue(m.b)
        self.assertIsNone(m.uid)

    def test_to_json(self):
        m = Mock(title="my title", b=True)
        m.num = 12
        m.channels = ['public']
        json_str = m.to_json()

        d = json.loads(json_str)
        self.assertIn('title', d)
        self.assertIn('title2', d)
        self.assertIn('num', d)
        self.assertIn('b', d)
        self.assertEqual(d['doc_type'], "mock")

    def test_doc_type(self):
        m = Mock(title="my title", b=True)
        m.channels = ['qwe']
        d = m.to_dict()
        self.assertEqual(d['doc_type'], "mock")

        m = Mock2(title="my title", b=True)
        m.channels = ['qwe']
        d = m.to_dict()
        self.assertEqual(d['doc_type'], "qwe")

    def test_from_json(self):
        m = Mock()
        m.from_json(json.dumps(dict(title="123", num=12, b=True)))
        self.assertEqual(m.title, "123")
        self.assertEqual(m.num, 12)
        self.assertEqual(m.b, True)

    def test_from_dict(self):
        m = Mock()
        m.from_dict(dict(title="123", num=12, b=True))
        self.assertEqual(m.title, "123")
        self.assertEqual(m.num, 12)
        self.assertEqual(m.b, True)

    def test_from_dict_bug(self):
        m = Transaction(channels=['boo'])
        m.amount = '12.34'
        m.save()

        m = Transaction(m.uid)
        self.assertEqual(m.amount, Decimal('12.34'))

        m.from_dict(dict(title="123"))
        self.assertEqual(m.amount, Decimal('12.34'))

    def test_save(self):
        m = Mock(title="my title", b=True)
        m.channels.append('channel')
        # empty
        self.assertIsNone(m.uid)
        self.assertIsNone(m.rev)
        m.save()
        # generated
        self.assertIsNotNone(m.uid)
        self.assertIsNotNone(m.rev)

        uid = m.uid
        rev = m.rev
        m.save()
        # not changed if save again
        self.assertEqual(uid, m.uid)
        # WAS changed
        self.assertNotEqual(rev, m.rev)

        rev = m.rev

        m = Mock(title="my title", b=True, uid=uid, rev=rev)
        m.channels.append('channel')
        self.assertEqual(uid, m.uid)
        self.assertIsNotNone(m.rev)
        m.save()
        self.assertEqual(uid, m.uid)
        self.assertNotEqual(rev, m.rev)

    def test_load(self):
        m = Mock(title="my title", b=True, num=12)
        m.channels.append(u'channel')
        m.save()

        uid = m.uid
        m = Mock()
        m.load(uid)

        self.assertEqual(m.title, "my title")
        self.assertEqual(m.num, 12)
        self.assertEqual(m.b, True)
        self.assertEqual(m.channels, [u'channel'])
        self.assertIsNotNone(m.uid)
        self.assertIsNotNone(m.rev)
        self.assertEqual(m.uid, uid)

    def test_load_2(self):
        m = Mock(title="my title", b=True, num=12)
        m.channels.append(u'channel')
        m.save()

        uid = m.uid

        m = Mock(uid)

        self.assertEqual(m.title, "my title")
        self.assertEqual(m.num, 12)
        self.assertEqual(m.b, True)
        self.assertEqual(m.channels, [u'channel'])
        self.assertIsNotNone(m.uid)
        self.assertIsNotNone(m.rev)
        self.assertEqual(m.uid, uid)

    def test_load_2_fails(self):
        m = Mock(title="my title", b=True, num=12)
        m.channels.append(u'channel')
        m.save()

        with self.assertRaises(SyncGatewayException):
            m = Mock('will fail')

    def test_prefix(self):
        m = Mock(title="my title", b=True, uid_prefix='job')
        m.channels = ['public']
        m.save()
        self.assertIn('job_', m.uid)

    def test_nested_dict(self):
        j = Job(title='my title')
        j.channels = ['public']
        p1 = Payment(amount=Decimal('12.34'))
        p2 = Payment(amount=Decimal('23.45'))
        j.payments = []
        j.payments.append(p1)
        j.payments.append(p2)
        j.payments.append(Payment(amount=Decimal('23.45'), uid='preset'))

        d = j.to_dict()

        self.assertEqual(d['title'], "my title")
        self.assertEqual(d['payments'][0]['amount'], '12.34')
        self.assertEqual(d['payments'][1]['amount'], '23.45')
        self.assertIsNotNone(d['payments'][0]['uid'])
        self.assertIsNotNone(d['payments'][1]['uid'])
        self.assertEqual(d['payments'][2]['uid'], 'preset')
        self.assertEqual(len(d['payments']), 3)

    def test_nested_save_load(self):
        j = Job(title='my title')
        j.channels = ['public']
        p1 = Payment(amount=Decimal('12.34'))
        p2 = Payment(amount=Decimal('23.45'))
        j.payments = []
        j.payments.append(p1)
        j.payments.append(p2)
        j.payments.append(Payment(amount=Decimal('23.45'), uid='preset'))
        # print j.to_dict()
        # return
        j.save()

        uid = j.uid

        j = Job()
        j.load(uid)

        self.assertEqual(j.title, "my title")
        self.assertEqual(j.payments[0].amount, Decimal('12.34'))
        self.assertEqual(j.payments[1].amount, Decimal('23.45'))
        self.assertIsNotNone(j.payments[0].uid)
        self.assertIsNotNone(j.payments[1].uid)
        self.assertEqual(j.payments[2].uid, 'preset')
        self.assertEqual(len(j.payments), 3)

    def test_query_related_objects(self):
        class Author(cbm.CouchbaseModel):
            class Meta:
                abstract = True
            doc_type = 'prn'

            full_name = models.CharField(max_length=255)

        class Article(cbm.CouchbaseModel):
            class Meta:
                abstract = True
            doc_type = 'chd'

            title = models.CharField(max_length=255)
            author_uid = models.CharField(max_length=255)

        channels = ['boo']

        au1 = Author(full_name='name1', channels=channels)
        au1.save()
        au2 = Author(full_name='name2', channels=channels)
        au2.save()
        au3 = Author(full_name='name3', channels=channels)
        au3.save()

        art1 = Article(title='title1', channels=channels)
        art1.author_uid = au1.uid
        art1.save()
        art2 = Article(title='title2', channels=channels)
        art2.author_uid = au2.uid
        art2.save()
        art3 = Article(title='title3', channels=channels)
        art3.author_uid = au3.uid
        art3.save()
        art4 = Article(title='title4', channels=channels)
        art4.author_uid = au3.uid
        art4.save()
        art5 = Article(title='title5', channels=channels)
        art5.author_uid = None
        art5.save()

        articles = [
            Article(art1.uid),
            Article(art2.uid),
            Article(art3.uid),
            Article(art4.uid),
            Article(art5.uid),
        ]

        load_related_objects(articles, 'author', Author)

        self.assertEqual(articles[0].author.uid, au1.uid)
        self.assertEqual(articles[1].author.uid, au2.uid)
        self.assertEqual(articles[2].author.uid, au3.uid)
        self.assertEqual(articles[3].author.uid, au3.uid)
        self.assertIsNone(articles[4].author)

    def test_datetime_null_saving(self):
        channels = ['boo']

        stamp = Stamp(channels=channels)
        stamp.save()

        stamp = Stamp(stamp.uid)
        self.assertIsNone(stamp.stamp)

    def test_datetime_naive_saving(self):
        channels = ['boo']
        now = datetime.now()

        stamp = Stamp(channels=channels)
        stamp.stamp = now
        stamp.save()

        stamp = Stamp(stamp.uid)
        self.assertEqual(stamp.stamp, now)

    def test_datetime_aware_saving(self):
        channels = ['boo']
        now = timezone.now()

        stamp = Stamp(channels=channels)
        stamp.stamp = now
        stamp.save()

        stamp = Stamp(stamp.uid)
        self.assertEqual(stamp.stamp, now)

    def test_decimal_null(self):
        channels = ['boo']

        money = Money(channels=channels)
        money.save()

        money = Money(money.uid)
        self.assertIsNone(money.amount)

    def test_decimal_amount(self):
        channels = ['boo']
        amount = Decimal('12.34')

        money = Money(channels=channels)
        money.amount = amount
        money.save()

        money = Money(money.uid)
        self.assertEqual(money.amount, amount)

    def test_decimal_amount_chars(self):
        channels = ['boo']
        amount_char = '12.34'
        amount = Decimal(amount_char)

        money = Money(channels=channels)
        money.amount = amount_char
        money.save()

        money = Money(money.uid)
        self.assertEqual(money.amount, amount)

    def test_decimal_amount_float(self):
        channels = ['boo']
        amount_float = '12.34'
        amount = Decimal(amount_float)

        money = Money(channels=channels)
        money.amount = amount_float
        money.save()

        money = Money(money.uid)
        self.assertEqual(money.amount, amount)


class SyncGatewayTestCase(TestCase):
    def setUp(self):
        from django_cbtools.management.commands.create_cb_views import Command

        SyncGateway.put_admin_user()
        command = Command()
        command.handle()

        # get random string to use as channel
        fake = Mock()
        self.channel = fake.get_uid()
        # print self.channel

        m = Mock(title="my title", b=True, num=12)
        m.channels.append(self.channel)
        m.save()
        self.uid1 = m.uid

        m = Mock(title="my title", b=True, num=12)
        m.channels.append(self.channel)
        m.save()
        self.uid2 = m.uid

    def test_query_objects(self):
        # import time
        # time.sleep(1)
        key = [self.channel, Mock.doc_type]
        query_objects('by_channel', key, Mock)

    def test_create_user(self):
        res = SyncGateway.put_user("username1", "email@mail.com", "password", ["public"])
        self.assertTrue(res)

    def test_delete_user(self):
        res = SyncGateway.put_user("username1", "email@mail.com", "password", ["public"])
        res = SyncGateway.delete_user("username1")
        self.assertTrue(res)
        with self.assertRaises(SyncGatewayException):
            SyncGateway.get_user("email@mail.com")

    def test_change_username(self):
        res = SyncGateway.put_user("email@mail.com", "email@mail.com", "password", ["public", 'boo'])
        res = SyncGateway.change_username("email@mail.com", "other_email@mail.com", "password")
        self.assertTrue(res)
        d = SyncGateway.get_user("other_email@mail.com")
        self.assertEqual(d['name'], "other_email@mail.com")
        self.assertEqual(d['email'], "other_email@mail.com")
        self.assertIn('boo', d['admin_channels'])
        with self.assertRaises(SyncGatewayException):
            SyncGateway.get_user("email@mail.com")

    def test_get_user(self):
        SyncGateway.put_user("email@mail.com", "email@mail.com", "password", ["public"])
        d = SyncGateway.get_user("email@mail.com")
        self.assertEqual(d['name'], "email@mail.com")
        self.assertEqual(d['email'], "email@mail.com")
