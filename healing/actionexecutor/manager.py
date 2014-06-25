# Copyright (c) 2010 OpenStack Foundation
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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
Action manager service
"""
from oslo.config import cfg
from healing import config
from oslo import messaging

from healing import context
from healing import exceptions
from healing.handler_manager import get_plugin_handler as handler_manager
from healing import manager
from healing.objects import action
from healing.engine.sla.manager import SLAAlarmingEngine
from healing.openstack.common import excutils
from healing.openstack.common import importutils
from healing.openstack.common import jsonutils
from healing.openstack.common import log as logging
from healing.openstack.common import periodic_task



LOG = logging.getLogger(__name__)
from healing import utils

class ActionManager(manager.Manager):
    target = messaging.Target(version='1.0')

    def __init__(self, scheduler_driver=None, *args, **kwargs):
        super(ActionManager, self).__init__(service_name='actionexecutor',
                                               *args, **kwargs)
        handler_manager()
        self.engine = SLAAlarmingEngine()

    def run_action(self, context, actions, block=False):
        if not type(actions) == list:
            actions = [actions]
        #if not context:
        #    context = utils.build_context()
        # remove, is for test
        context = utils.build_context()
        return handler_manager().start_plugins_group(context, actions,
                                                     block=block)

    def alarm(self, ctxt, alarm_id, source=None, contract_id=None, resource_id=None,
              project_id=None):
        # TODO: check why token is not there, from notification my be ok , but 
        # from API is still the same?
        if ctxt.token is None:
            ctxt = utils.build_context()
        self.engine.alert(ctxt, alarm_id, source, contract_id=contract_id, 
                          resource_id=resource_id, project_id=project_id)

