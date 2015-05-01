# Copyright 2012 Nebula, Inc.
#
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import functools

from oslo_utils import timeutils

from keystoneauth.i18n import _
from keystoneauth import service_catalog
from keystoneauth import utils


# gap, in seconds, to determine whether the given token is about to expire
STALE_TOKEN_DURATION = 30


@utils.positional()
def create(resp=None, body=None, auth_token=None):
    if resp and not body:
        body = resp.json()

    if 'token' in body:
        if resp and not auth_token:
            auth_token = resp.headers.get('X-Subject-Token')

        return AccessInfoV3(body, auth_token)
    elif 'access' in body:
        return AccessInfoV2(body, auth_token)

    raise ValueError(_('Unrecognized auth response'))


def missingproperty(f):

    @functools.wraps(f)
    def inner(self):
        try:
            return f(self)
        except KeyError:
            return None

    return property(inner)


class AccessInfo(object):
    """Encapsulates a raw authentication token from keystone.

    Provides helper methods for extracting useful values from that token.

    """

    _service_catalog_class = None

    def __init__(self, body, auth_token=None):
        self._data = body
        self._auth_token = auth_token
        self._service_catalog = None

    @property
    def service_catalog(self):
        if not self._service_catalog:
            self._service_catalog = self._service_catalog_class.from_token(
                self._data)

        return self._service_catalog

    def will_expire_soon(self, stale_duration=None):
        """Determines if expiration is about to occur.

        :returns: true if expiration is within the given duration
        :rtype: boolean

        """
        stale_duration = (STALE_TOKEN_DURATION if stale_duration is None
                          else stale_duration)
        norm_expires = timeutils.normalize_time(self.expires)
        # (gyee) should we move auth_token.will_expire_soon() to timeutils
        # instead of duplicating code here?
        soon = (timeutils.utcnow() + datetime.timedelta(
                seconds=stale_duration))
        return norm_expires < soon

    def has_service_catalog(self):
        """Returns true if the authorization token has a service catalog.

        :returns: boolean
        """
        raise NotImplementedError()

    @property
    def auth_token(self):
        """Returns the token_id associated with the auth request, to be used
        in headers for authenticating OpenStack API requests.

        :returns: str
        """
        return self._auth_token

    @property
    def expires(self):
        """Returns the token expiration (as datetime object)

        :returns: datetime
        """
        raise NotImplementedError()

    @property
    def issued(self):
        """Returns the token issue time (as datetime object)

        :returns: datetime
        """
        raise NotImplementedError()

    @property
    def username(self):
        """Returns the username associated with the authentication request.
        Follows the pattern defined in the V2 API of first looking for 'name',
        returning that if available, and falling back to 'username' if name
        is unavailable.

        :returns: str
        """
        raise NotImplementedError()

    @property
    def user_id(self):
        """Returns the user id associated with the authentication request.

        :returns: str
        """
        raise NotImplementedError()

    @property
    def user_domain_id(self):
        """Returns the domain id of the user associated with the authentication
        request.

        :returns: str
        """
        raise NotImplementedError()

    @property
    def user_domain_name(self):
        """Returns the domain name of the user associated with the
        authentication request.

        :returns: str
        """
        raise NotImplementedError()

    @property
    def role_ids(self):
        """Returns a list of role ids of the user associated with the
        authentication request.

        :returns: a list of strings of role ids
        """
        raise NotImplementedError()

    @property
    def role_names(self):
        """Returns a list of role names of the user associated with the
        authentication request.

        :returns: a list of strings of role names
        """
        raise NotImplementedError()

    @property
    def domain_name(self):
        """Returns the domain name associated with the authentication token.

        :returns: str or None (if no domain associated with the token)
        """
        raise NotImplementedError()

    @property
    def domain_id(self):
        """Returns the domain id associated with the authentication token.

        :returns: str or None (if no domain associated with the token)
        """
        raise NotImplementedError()

    @property
    def project_name(self):
        """Returns the project name associated with the authentication request.

        :returns: str or None (if no project associated with the token)
        """
        raise NotImplementedError()

    @property
    def tenant_name(self):
        """Synonym for project_name."""
        return self.project_name

    @property
    def scoped(self):
        """Returns true if the authorization token was scoped to a tenant
           (project), and contains a populated service catalog.

           This is deprecated, use project_scoped instead.

        :returns: bool
        """
        return self.project_scoped or self.domain_scoped

    @property
    def project_scoped(self):
        """Returns true if the authorization token was scoped to a tenant
           (project).

        :returns: bool
        """
        raise NotImplementedError()

    @property
    def domain_scoped(self):
        """Returns true if the authorization token was scoped to a domain.

        :returns: bool
        """
        raise NotImplementedError()

    @property
    def trust_id(self):
        """Returns the trust id associated with the authentication token.

        :returns: str or None (if no trust associated with the token)
        """
        raise NotImplementedError()

    @property
    def trust_scoped(self):
        """Returns true if the authorization token was scoped as delegated in a
        trust, via the OS-TRUST v3 extension.

        :returns: bool
        """
        raise NotImplementedError()

    @property
    def trustee_user_id(self):
        """Returns the trustee user id associated with a trust.

        :returns: str or None (if no trust associated with the token)
        """
        raise NotImplementedError()

    @property
    def trustor_user_id(self):
        """Returns the trustor user id associated with a trust.

        :returns: str or None (if no trust associated with the token)
        """
        raise NotImplementedError()

    @property
    def project_id(self):
        """Returns the project ID associated with the authentication
        request, or None if the authentication request wasn't scoped to a
        project.

        :returns: str or None (if no project associated with the token)
        """
        raise NotImplementedError()

    @property
    def tenant_id(self):
        """Synonym for project_id."""
        return self.project_id

    @property
    def project_domain_id(self):
        """Returns the domain id of the project associated with the
        authentication request.

        :returns: str
        """
        raise NotImplementedError()

    @property
    def project_domain_name(self):
        """Returns the domain name of the project associated with the
        authentication request.

        :returns: str
        """
        raise NotImplementedError()

    @property
    def oauth_access_token_id(self):
        """Return the access token ID if OAuth authentication used.

        :returns: str or None.
        """
        raise NotImplementedError()

    @property
    def oauth_consumer_id(self):
        """Return the consumer ID if OAuth authentication used.

        :returns: str or None.
        """
        raise NotImplementedError()

    @property
    def is_federated(self):
        """Returns true if federation was used to get the token.

        :returns: boolean
        """
        raise NotImplementedError()

    @property
    def audit_id(self):
        """Return the audit ID if present.

        :returns: str or None.
        """
        raise NotImplementedError()

    @property
    def audit_chain_id(self):
        """Return the audit chain ID if present.

        In the event that a token was rescoped then this ID will be the
        :py:attr:`audit_id` of the initial token. Returns None if no value
        present.

        :returns: str or None.
        """
        raise NotImplementedError()

    @property
    def initial_audit_id(self):
        """The audit ID of the initially requested token.

        This is the :py:attr:`audit_chain_id` if present or the
        :py:attr:`audit_id`.
        """
        return self.audit_chain_id or self.audit_id


class AccessInfoV2(AccessInfo):
    """An object for encapsulating a raw v2 auth token from identity
       service.
    """

    version = 'v2.0'
    _service_catalog_class = service_catalog.ServiceCatalogV2

    def has_service_catalog(self):
        return 'serviceCatalog' in self

    @missingproperty
    def auth_token(self):
        set_token = super(AccessInfoV2, self).auth_token
        return set_token or self._data['access']['token']['id']

    @missingproperty
    def _token(self):
        return self._data['access']['token']

    @missingproperty
    def expires(self):
        return timeutils.parse_isotime(self._token.get('expires'))

    @missingproperty
    def issued(self):
        return self._token['issued_at']

    @property
    def _user(self):
        return self._data['access']['user']

    @missingproperty
    def username(self):
        return self._user.get('name') or self._user.get('username')

    @missingproperty
    def user_id(self):
        return self._user['id']

    @property
    def user_domain_id(self):
        return None

    @property
    def user_domain_name(self):
        return None

    @missingproperty
    def role_ids(self):
        return self.get('metadata', {}).get('roles', [])

    @missingproperty
    def role_names(self):
        return [r['name'] for r in self._user.get('roles', [])]

    @property
    def domain_name(self):
        return None

    @property
    def domain_id(self):
        return None

    @property
    def project_name(self):
        try:
            tenant_dict = self._token['tenant']
        except KeyError:
            pass
        else:
            return tenant_dict.get('name')

        # pre grizzly
        try:
            return self._user['tenantName']
        except KeyError:
            pass

        # pre diablo, keystone only provided a tenantId
        try:
            return self._token['tenantId']
        except KeyError:
            pass

    @property
    def project_scoped(self):
        return 'tenant' in self._token

    @property
    def domain_scoped(self):
        return False

    @property
    def _trust(self):
        return self._data['access']['trust']

    @missingproperty
    def trust_id(self):
        return self._trust['id']

    @property
    def trust_scoped(self):
        return bool(self._trust)

    @missingproperty
    def trustee_user_id(self):
        return self._trust['trustee_user_id']

    @property
    def trustor_user_id(self):
        # this information is not available in the v2 token bug: #1331882
        return None

    @property
    def project_id(self):
        try:
            tenant_dict = self._token['tenant']
        except KeyError:
            pass
        else:
            return tenant_dict.get('id')

        # pre grizzly
        try:
            return self._user['tenantId']
        except KeyError:
            pass

        # pre diablo
        try:
            return self._token['tenantId']
        except KeyError:
            pass

    @property
    def project_domain_id(self):
        return None

    @property
    def project_domain_name(self):
        return None

    @property
    def oauth_access_token_id(self):
        return None

    @property
    def oauth_consumer_id(self):
        return None

    @property
    def is_federated(self):
        return False

    @property
    def audit_id(self):
        try:
            return self._token.get('audit_ids', [])[0]
        except IndexError:
            return None

    @property
    def audit_chain_id(self):
        try:
            return self._token.get('audit_ids', [])[1]
        except IndexError:
            return None


class AccessInfoV3(AccessInfo):
    """An object for encapsulating a raw v3 auth token from identity
       service.
    """

    version = 'v3'
    _service_catalog_class = service_catalog.ServiceCatalogV3

    def has_service_catalog(self):
        return 'catalog' in self._data['token']

    @property
    def _user(self):
        return self._data['token']['user']

    @property
    def is_federated(self):
        return 'OS-FEDERATION' in self._user

    @missingproperty
    def expires(self):
        return timeutils.parse_isotime(self._data['token']['expires_at'])

    @missingproperty
    def issued(self):
        return timeutils.parse_isotime(self._data['token']['issued_at'])

    @missingproperty
    def user_id(self):
        return self._user['id']

    @property
    def user_domain_id(self):
        try:
            return self._user['domain']['id']
        except KeyError:
            if self.is_federated:
                return None
            raise

    @property
    def user_domain_name(self):
        try:
            return self._user['domain']['name']
        except KeyError:
            if self.is_federated:
                return None
            raise

    @missingproperty
    def role_ids(self):
        return [r['id'] for r in self._data['token'].get('roles', [])]

    @missingproperty
    def role_names(self):
        return [r['name'] for r in self._data['token'].get('roles', [])]

    @missingproperty
    def username(self):
        return self._user['name']

    @missingproperty
    def _domain(self):
        return self._data['token']['domain']

    @missingproperty
    def domain_name(self):
        return self._domain['name']

    @missingproperty
    def domain_id(self):
        return self._domain['id']

    @property
    def _project(self):
        return self._data['token']['project']

    @missingproperty
    def project_id(self):
        return self._project['id']

    @missingproperty
    def project_domain_id(self):
        return self._project['domain']['id']

    @property
    def project_domain_name(self):
        return self._project['domain']['name']

    @missingproperty
    def project_name(self):
        return self._project['name']

    @property
    def project_scoped(self):
        try:
            return bool(self._project)
        except KeyError:
            return False

    @property
    def domain_scoped(self):
        try:
            return bool(self._domain)
        except KeyError:
            return False

    @property
    def _trust(self):
        return self._data['token']['OS-TRUST:trust']

    @missingproperty
    def trust_id(self):
        return self._trust['id']

    @property
    def trust_scoped(self):
        try:
            return bool(self._trust)
        except KeyError:
            return False

    @missingproperty
    def trustee_user_id(self):
        return self._trust['trustee_user']['id']

    @missingproperty
    def trustor_user_id(self):
        return self._trust['trustor_user']['id']

    @property
    def _oauth(self):
        return self._data['token']['OS-OAUTH1']

    @missingproperty
    def oauth_access_token_id(self):
        return self._oauth['access_token_id']

    @missingproperty
    def oauth_consumer_id(self):
        return self._oauth['consumer_id']

    @missingproperty
    def audit_id(self):
        try:
            return self._data['token']['audit_ids'][0]
        except IndexError:
            return None

    @missingproperty
    def audit_chain_id(self):
        try:
            return self._data['token']['audit_ids'][1]
        except IndexError:
            return None
