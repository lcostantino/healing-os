# Copyright 2013, Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Client side of the action manager RPC API.
"""

from oslo.config import cfg
from healing import config
from oslo import messaging

from healing.objects import base as objects_base
from healing.openstack.common import jsonutils
from healing.rpc import rpc

CONF = config.CONF
rpcapi_cap_opt = cfg.StrOpt('actionmanager',
        default='1.0',
        help='Set a version cap for messages sent to action services')
CONF.register_opt(rpcapi_cap_opt, 'upgrade_levels')

class ActionAPI(object):
    '''Client side 

    API version history:

        1.0 - Initial version.    '''

    VERSION_ALIASES = {}

    def __init__(self):
        super(ActionAPI, self).__init__()
        target = messaging.Target(topic=CONF.action_executor.topic, version='1.0')
        version_cap = self.VERSION_ALIASES.get(CONF.upgrade_levels.actionmanager,
                                               CONF.upgrade_levels.actionmanager)
        serializer = objects_base.HealingObjectSerializer()
        self.client = rpc.get_client(target, version_cap=version_cap,
                                     serializer=serializer)

    def run_action(self, ctxt, actions, block=False):
        cctxt = self.client.prepare()
        cctxt.cast(ctxt, 'run_action', actions=actions, block=block)

    def run_action_and_wait(self, ctxt, actions, block=False):
        cctxt = self.client.prepare()
        cctxt.call(ctxt, 'run_action', actions=actions, block=block)

    def alarm(self, ctxt, alarm_id, source=None, contract_id=None,
              resource_id=None, project_id=None):
        cctxt = self.client.prepare()
        cctxt.cast(ctxt, 'alarm', alarm_id=alarm_id, source=source,
                   contract_id=contract_id, resource_id=resource_id,
                   project_id=project_id)
