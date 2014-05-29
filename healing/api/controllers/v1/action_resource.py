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

from wsme import types as wtypes
from healing.api.controllers import resource


class Action(resource.Resource):
    """when handler resource."""

    name = wtypes.text
    description = wtypes.text
    #TODO: retrieve enable/disble from stevedore?
    status = wtypes.text


class Actionsresource.Resource):
    """A collection of handlers."""

    actions  = [Action]


class ActionsController(rest.RestController):

    @wsme_pecan.wsexpose(Handlers)
    def get_all(self):
        LOG.debug("Fetch handlers plugins")
        manager = get_plugin_handler()

        handlers = [Handler.from_dict(values)
                    for values in manager.plugin_list()]

        return Actions(actions=actions)
