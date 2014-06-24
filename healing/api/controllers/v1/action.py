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
from pecan import abort
from pecan import rest
import wsmeext.pecan as wsme_pecan
from wsme import types as wtypes

from healing.openstack.common import log as logging

from healing.api.controllers import resource
from healing import exceptions
from healing.objects import action
from healing import utils
from healing import context

LOG = logging.getLogger(__name__)

class ActionResource(resource.Resource):
    """Action Resource."""

    id = wtypes.text
    created_at = wtypes.datetime.datetime
    name = wtypes.text
    status = wtypes.text
    request_id = wtypes.text
    output = wtypes.text
    action_meta = wtypes.text
    project_id = wtypes.text
    target_id = wtypes.text


class ActionList(resource.Resource):
    actions = [ActionResource]


class ActionsController(rest.RestController):

    @wsme_pecan.wsexpose(ActionList, wtypes.text, wtypes.text)
    def get_all(self, request_id=None, name=None):
        ctx = utils.get_context_req(pecan.request)
        if request_id:
            ret = action.Action.get_all_by_request_id(request_id)
        elif name:
            ret = action.Action.get_all_by_name(name)
        else:
            # TODO: do a limit then... and pagination
            ret = action.Action.get_all()

        actions =  [ActionResource.from_obj(x) for x in ret]
        return ActionList(actions=actions)

    @wsme_pecan.wsexpose(body=ActionResource, status_code=201)
    def post(self, act):
        if ActionResource.name and \
           ActionResource.request_id and \
           ActionResource.target_id and \
           ActionResource.status:
            action_obj = action.Action.from_dict(act.to_dict())
            action_obj.create()
        else:
            abort(400, 'Name, request_id and target_id are required')
