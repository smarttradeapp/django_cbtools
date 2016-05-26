import json
import logging
import requests
from requests.auth import HTTPBasicAuth

from django.conf import settings

logger = logging.getLogger(__name__)


class SyncGatewayException(Exception):
    pass


class SyncGatewayConflict(SyncGatewayException):
    pass


class SyncGateway(object):
    @staticmethod
    def put_user(username, email=None, password=None, admin_channels=None, disabled=False):
        from .models import CHANNEL_PUBLIC

        url = '%s/%s/_user/%s' % (settings.SYNC_GATEWAY_ADMIN_URL,
                                  settings.SYNC_GATEWAY_BUCKET,
                                  username)

        if admin_channels is None:
            admin_channels = []

        if CHANNEL_PUBLIC not in admin_channels:
            admin_channels.append(CHANNEL_PUBLIC)

        dict_payload = dict(admin_channels=admin_channels,
                            disabled=disabled)
        if email is not None:
            dict_payload['email'] = email

        if password is not None:
            dict_payload['password'] = password

        json_payload = json.dumps(dict_payload)
        response = requests.put(url, data=json_payload, verify=False)
        if response.status_code not in [200, 201]:
            raise SyncGatewayException("Can not create / update sg-user, response code: %d" % response.status_code)

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
    def get_users():
        url = '%s/%s/_user/' % (settings.SYNC_GATEWAY_ADMIN_URL,
                                settings.SYNC_GATEWAY_BUCKET)

        response = requests.get(url, verify=False)
        if response.status_code not in [200, 201]:
            raise SyncGatewayException("Can not get users, response code: %d" % response.status_code)

        return response.json()

    @staticmethod
    def change_username(old_username, new_username, password):
        if old_username == new_username:
            return False

        json_payload = SyncGateway.get_user(old_username)
        SyncGateway.put_user(username=new_username,
                             email=new_username,
                             password=password,
                             admin_channels=json_payload['admin_channels'],
                             disabled=False)
        SyncGateway.delete_user(old_username)
        return True

    @staticmethod
    def create_session(username, ttl=None):
        url = '%s/%s/_session' % (settings.SYNC_GATEWAY_ADMIN_URL,
                                  settings.SYNC_GATEWAY_BUCKET)

        dict_payload = dict(name=username)

        if ttl is not None:
            dict_payload['ttl'] = ttl

        json_payload = json.dumps(dict_payload)
        response = requests.post(url, data=json_payload, verify=False)

        if response.status_code != 200:
            message = "Can not create session for sg-user (%s), response code: %d" % (username, response.status_code)
            raise SyncGatewayException(message)
        return response

    @staticmethod
    def delete_user(username):
        url = '%s/%s/_user/%s' % (settings.SYNC_GATEWAY_ADMIN_URL,
                                  settings.SYNC_GATEWAY_BUCKET,
                                  username)

        response = requests.delete(url, verify=False)
        if response.status_code not in [200, 201]:
            raise SyncGatewayException("Can not delete user, response code: %d" % response.status_code)

        return True

    @staticmethod
    def append_channels(username, channels):
        json_payload = SyncGateway.get_user(username)
        new_channels = set(json_payload['admin_channels'])
        new_channels.update(channels)
        return SyncGateway.put_user(username=username, admin_channels=list(new_channels))

    @staticmethod
    def remove_channels(username, channels):
        json_payload = SyncGateway.get_user(username)
        new_channels = set(json_payload['admin_channels'])
        new_channels.difference_update(channels)
        return SyncGateway.put_user(username=username, admin_channels=list(new_channels))

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

            msg = "Can not save document %s, response code: %d" % (document, response.status_code)

            if response.status_code == 409:
                raise SyncGatewayConflict(msg)

            raise SyncGatewayException(msg)

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
