# -*- encoding: utf-8 -*-
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
"""Load plugins
"""

from stevedore import extension
from healing.openstack.common import log

LOG = log.getLogger(__name__)


CURRENT_HANDLER = None


class HandlerManager(object):

    def __init__(self):
        self.mgr = extension.ExtensionManager(namespace='healing.handlers',
                                              invoke_on_load=True,
                                              invoke_args=(),)

    def plugin_list(self):
        data_plugins = []
        for x in self.mgr:
            data_plugins.append({'name': x.name,
                                 'description': x.plugin.DESCRIPTION})
        return data_plugins

    def get_plugin(self, name):
        try:
            return self.mgr[name].plugin
            #add pluginnotfound
        except Exception:
            raise


def get_plugin_handler():
    global CURRENT_HANDLER
    if not CURRENT_HANDLER:
        CURRENT_HANDLER = HandlerManager()
    return CURRENT_HANDLER
