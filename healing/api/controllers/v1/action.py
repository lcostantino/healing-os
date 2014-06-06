# -*- coding: utf-8 -*-
#
# Copyright 2013 - Intel
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

import pecan
from pecan import rest
import wsmeext.pecan as wsme_pecan

from healing.openstack.common import log as logging


from healing import exceptions
from healing.handler_manager import get_plugin_handler
from healing.handler_plugins import base
from healing import data_convert
from healing import utils
from healing import context

LOG = logging.getLogger(__name__)

class ActionsController(rest.RestController):

    @wsme_pecan.wsexpose()
    def get_all(self):
        LOG.debug("List actions --- ")
         # sample of get a context - in auth disabled will create
        # admin context from config file
        ctx = utils.get_context_req(pecan.request)
        mg = get_plugin_handler()
        
        to_run = []
        for x in range(1,10):
            to_run.append(base.ActionData(name='evacuate', target_resource='s', data={}))
                
                
                
        print(mg.start_plugins_group(ctx, to_run))
                
                
        #client = utils.get_ceilometer_client(ctx)
        #print client.alarms.list()
        """
        from healing.engine import alarm
        cm = alarm.CeilometerAlarm(ctx=ctx, contract_id='111', action='evacuate',
                             meter='cpu_util', threshold=1,
                             operator='eq',  period=10)
        cm.create()
        """
        return "actions"
