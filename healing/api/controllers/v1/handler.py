# -*- coding: utf-8 -*-
#
# Copyright 2014 - Intel
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
from pecan import abort
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from healing.openstack.common import log as logging
from healing.api.controllers import resource
from healing.api import types
from healing import exceptions
from healing.handler_manager import get_plugin_handler
from healing import data_convert
from healing import utils
from healing import context

LOG = logging.getLogger(__name__)


class Handler(resource.Resource):
    """Handler resource."""
    name = wtypes.text
    description = wtypes.text
    #TODO: retrieve enable/disble from stevedore?
    status = wtypes.text


class Handlers(resource.Resource):
    """A collection of handlers."""
    handlers = [Handler]


class HandlersController(rest.RestController):

    @wsme_pecan.wsexpose(Handlers)
    def get_all(self):
        LOG.debug("Fetch handlers plugins")
        manager = get_plugin_handler()

        handlers = [Handler.from_dict(values)
                    for values in manager.plugin_list()]

        return Handlers(handlers=handlers)

    @wsme_pecan.wsexpose(None, wtypes.text, wtypes.text, wtypes.text)
    def get(self, name, target_resource, source='custom'):
        return self.post(name, source, target_resource, None)

    # TODO:cannot coerce body right now, wtypes not supported and want
    # dynamic...
    # add target_resource as param optional
    #@api_utils.translate_exceptions()
    @wsme_pecan.wsexpose(wtypes.text, wtypes.text, wtypes.text, wtypes.text, None)
    def post(self, name, source='custom', target_resource=None, data=None):
        LOG.debug('POST plugin ' + name + ':' + source + ':')
        manager = get_plugin_handler()
        try:
            plugin = manager.check_plugin_name(name)

            conversor = data_convert.FormatterBase.get_formatter(source)

        except exceptions.InvalidSourceException as e:
            LOG.exception(e)
            abort(500, e.message)
        except Exception as e:
            #add conversor not found, pluginnotfound exception
            LOG.exception(e)
            abort(404, e.message)
        #if ceilometer, fetch header data and resource
        #if custom, just expose data
        #source converter(source, extra_data, headers)

        #TODO: normalize data in object?
        action_data = conversor.format(name, data,
                                       target_resource=target_resource,
                                       headers=pecan.request.headers)
        LOG.debug(action_data)
        #TODO: Retrieve context if token in header from middleware
        #Should be done on authorization? If not provided used admin
        #build context should not call authorize in that case
        ctx = utils.build_context(None, True)
        return {'action_id': manager.start_plugin(name, ctx=ctx, data=action_data)}


