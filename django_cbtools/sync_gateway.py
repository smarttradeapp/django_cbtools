import json
import logging
import requests
from requests.auth import HTTPBasicAuth

from django.conf import settings

logger = logging.getLogger(__name__)


class SyncGatewayException(Exception):
    pass


class SyncGateway(object):
    @staticmethod
    def put_user(username, email, password, admin_channels, disabled=False):
        from .models import CHANNEL_PUBLIC

        url = '%s/%s/_user/%s' % (settings.SYNC_GATEWAY_ADMIN_URL,
                                  settings.SYNC_GATEWAY_BUCKET,
                                  username)

        if CHANNEL_PUBLIC not in admin_channels:
            admin_channels.append(CHANNEL_PUBLIC)

        dict_payload = dict(admin_channels=admin_channels,
                            disabled=disabled)
        if email:
            dict_payload['email'] = email

        if password:
            dict_payload['password'] = password

        json_payload = json.dumps(dict_payload)
        response = requests.put(url, data=json_payload, verify=False)
        if response.status_code not in [200, 201]:
            raise SyncGatewayException("Can not create user, response code: %d" % response.status_code)

        return True

    @staticmethod
    def get_user(username):
        url = '%s/%s/_user/%s' % (settings.SYNC_GATEWAY_ADMIN_URL,
                                  settings.SYNC_GATEWAY_BUCKET,
                                  username)

        response = requests.get(url, verify=False)
        if response.status_code not in [200, 201]:
            raise SyncGatewayException("Can not get user (%s), response code: %d" % (username, response.status_code))

        return response.json()

    @staticmethod
    def change_username(old_username, new_username, password):
        json_payload = SyncGateway.get_user(old_username)
        SyncGateway.delete_user(old_username)
        return SyncGateway.put_user(username=new_username,
                                    email=new_username,
                                    password=password,
                                    admin_channels=json_payload['admin_channels'],
                                    disabled=False)

    @staticmethod
    def delete_user(username):
        url = '%s/%s/_user/%s' % (settings.SYNC_GATEWAY_ADMIN_URL,
                                  settings.SYNC_GATEWAY_BUCKET,
                                  username)

        response = requests.delete(url, verify=False)
        if response.status_code not in [200, 201]:
            raise SyncGatewayException("Can not delete user, response code: %d" % response.status_code)

        return True

    # def get_user(self, username):
    #     url = '%s/%s/_user/%s' % (settings.SYNC_GATEWAY_ADMIN_URL,
    #                               settings.SYNC_GATEWAY_BUCKET,
    #                               username)
    #     return requests.put(url)

    @staticmethod
    def put_admin_user():
        username = settings.SYNC_GATEWAY_USER
        password = settings.SYNC_GATEWAY_PASSWORD
        SyncGateway.put_user(username, "smadmin@mail.com", password, ["*"])

    @staticmethod
    def put_guest_user():
        from .models import CHANNEL_PUBLIC
        username = settings.SYNC_GATEWAY_GUEST_USER
        password = settings.SYNC_GATEWAY_GUEST_PASSWORD
        SyncGateway.put_user(username, "smguest@mail.com", password, [CHANNEL_PUBLIC])

    @staticmethod
    def save_json(uid, data_dict):
        """
        Saves dictinary `data_dict` to database via SyncGateway
        """
        json_payload = json.dumps(data_dict)
        url = '%s/%s/%s' % (settings.SYNC_GATEWAY_URL,
                            settings.SYNC_GATEWAY_BUCKET,
                            uid)

        return requests.put(url, data=json_payload, auth=SyncGateway.get_auth(), verify=False)

    @staticmethod
    def save_document(document):
        data_dict = document.to_dict()
        if hasattr(document, 'rev') and document.rev:
            data_dict['_rev'] = document.rev

        response = SyncGateway.save_json(document.get_uid(), data_dict)

        if response.status_code not in [200, 201]:
            rev = document.rev if hasattr(document, 'rev') else 'n/a'
            logger.error('error on doc saving, status {}, revision {}, uid {}'.format(
                         response.status_code, rev, document.get_uid()))
            raise SyncGatewayException("Can not save document %s, response code: %d" % (document, response.status_code))

        d = response.json()

        document.rev = d['rev']

    @staticmethod
    def delete_document(uid, rev):
        url = '%s/%s/%s?rev=%s' % (settings.SYNC_GATEWAY_URL,
                                   settings.SYNC_GATEWAY_BUCKET,
                                   uid, rev)

        response = requests.delete(url, auth=SyncGateway.get_auth(), verify=False)

        if response.status_code not in [200, 201]:
            raise SyncGatewayException("Can not delete document %s, response code: %d" % (uid, response.status_code))

    @staticmethod
    def all_docs(uids, really_all=False):
        if not uids and not really_all:
            return {"rows": []}

        url = '%s/%s/_all_docs?include_docs=true' % (settings.SYNC_GATEWAY_URL,
                                                     settings.SYNC_GATEWAY_BUCKET)

        json_data = json.dumps(dict(keys=uids)) if uids else None
        response = requests.post(url, data=json_data,
                                 auth=SyncGateway.get_auth(),
                                 verify=False)

        # print response.json()
        return response.json()

    @staticmethod
    def get_auth():
        return HTTPBasicAuth(settings.SYNC_GATEWAY_USER,
                             settings.SYNC_GATEWAY_PASSWORD)


# def ss():
#     from .connection import connection
#     c = connection()
#     j = SyncGateway.all_docs(None, really_all=True)

#     # r = []
#     # print json
#     for row in j['rows']:
#         doc = row['doc']
#         # print doc
#         if 'doc_type' in doc and doc['doc_type'] == 'job':
#             # print doc['doc_type']
#             # continue
#             if 'customer_uid' in doc:
#                 if 'job' in doc['customer_uid']:
#                     print doc['customer_uid']
#                     c.delete(doc['customer_uid'])
#                     print 'deleted'
