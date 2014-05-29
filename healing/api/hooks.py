# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
#
# Author: Doug Hellmann <doug.hellmann@dreamhost.com>
#         Angus Salkeld <asalkeld@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import threading

from oslo.config import cfg
from pecan import hooks

class ConfigHook(hooks.PecanHook):
    """Attach the configuration object to the request
    so controllers can get to it.
    """

    def before(self, state):
        state.request.cfg = cfg.CONF


class DBHook(hooks.PecanHook):

    def __init__(self, storage_connection):
        self.storage_connection = storage_connection

    def before(self, state):
        state.request.storage_conn = self.storage_connection

class TranslationHook(hooks.PecanHook):

    def __init__(self):
        # Use thread local storage to make this thread safe in situations
        # where one pecan instance is being used to serve multiple request
        # threads.
        self.local_error = threading.local()
        self.local_error.translatable_error = None

    def before(self, state):
        self.local_error.translatable_error = None

    def after(self, state):
        if hasattr(state.response, 'translatable_error'):
            self.local_error.translatable_error = (
                state.response.translatable_error)


class ErrorHook(hooks.PecanHook):
    def on_error(self, state, exc):
        if isinstance(exc, exceptions.AuthorizationException):
            return webob.Response('Not Authorized', status=401)
        if isinstance(exc, exceptions.InvalidDataException):
            return webob.Response(exc.message, status=500)

