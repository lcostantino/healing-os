# -*- coding: utf-8 -*-
#
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""Access Control API server."""

from keystoneclient.middleware import auth_token
from oslo.config import cfg
from pecan.hooks import PecanHook
import re
import webob

from healing import config
from healing import exceptions
from healing import utils
from healing.openstack.common import log as logging

LOG = logging.getLogger(__name__)

def setup(app):
    if cfg.CONF.pecan.auth_enable:
        return auth_token.AuthProtocol(app, conf=dict(cfg.CONF.keystone))
    else:
        return app


def is_valid_admin_user(headers):
    if not valid_access(headers):
        return False
    return 'admin' in headers.get('X-Roles').split(',')


def valid_access(headers):
    if headers.get('X-Identity-Status', 'Invalid') == 'Invalid':
        LOG.debug('No valid access')
        return False
    return True


def get_limited_to(headers):
    """Return the user and project the request should be limited to.

    :param headers: HTTP headers dictionary
    :return: A tuple of (user, project), set to None if there's no limit on
    one of these.

    """
    return headers.get('X-User-Id'), headers.get('X-Project-Id')


def get_limited_to_project(headers):
    """Return the project the request should be limited to.

    :param headers: HTTP headers dictionary
    :return: A project, or None if there's no limit on it.

    """
    return get_limited_to(headers)[1]


class DelayedAuthHook(PecanHook):
    """
    Validate authorization from delayed keystone if url
    is not whitelisted
    """
    WHITELIST = []
    def __init__(self):
        self.WHITELIST = [url.strip() for url in
                config.CONF.api.unauthorized_urls if url]

    def _should_authorize_url(self, url):
        for i in self.WHITELIST:
            if re.match(i.strip(), url):
                raise Exception(str(i) + "|" + str(url))
                LOG.debug("URL authorization not required %s" % url)
                return False
        return True

    def before(self, state):
        if not config.CONF.pecan.auth_enable:
            state.request.admin_ctx = utils.build_context()
            return
        if self._should_authorize_url(state.request.url) and \
            not is_valid_admin_user(state.request.headers):
            # (TODO) add log
            raise exceptions.AuthorizationException('Required admin')

        state.request.admin_ctx = utils.context_from_headers(
                                                        state.request.headers)


class ErrorHook(PecanHook):
    def on_error(self, state, exc):
        if isinstance(exc, exceptions.AuthorizationException):
            return webob.Response('Not Authorized', status=401)

