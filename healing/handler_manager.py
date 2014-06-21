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
from healing import exceptions
from healing import task_scheduler as scheduler

from healing.handler_plugins import plugin_config
from healing.openstack.common import log
from healing.openstack.common import threadgroup

LOG = log.getLogger(__name__)


CURRENT_HANDLER = None
class HandlerManager(object):

    def __init__(self):
        self.mgr = extension.ExtensionManager(namespace='healing.handlers',
                                              invoke_on_load=True,
                                              invoke_args=(),)
        self.restrictions = extension.ExtensionManager(
                                namespace='healing.handler_restrictions',
                                invoke_on_load=False,
                                invoke_args=(),)
        self.setup_config()
        self.thread_pool = threadgroup.ThreadGroup(thread_pool_size=5)

    def setup_config(self):
        plain_data = {}
        for x in self.restrictions:
            plain_data[x.name] = x.plugin.CFG_PARAMS
        plugin_names = [x.name for x in self.mgr]
        self.config_manager = plugin_config.setup_config(plain_data,
                                                         plugin_names)

    def plugin_list(self):
        data_plugins = []
        for x in self.mgr:
            data_plugins.append({'name': x.name,
                                 'description': x.plugin.DESCRIPTION})
        return data_plugins

    def can_execute(self, name, *args, **kwargs):
        """ Check restrictions associated to the plugin.
            Right now we cannot combine results neither set a mandatory check
            as superset result.
            With only one TRUE we stop the check and start execution,
            because this are logical restrictions with dependencies
            need to think about it...
        """
        checks = self.config_manager.get_restriction_config_for(name)
        if not checks:
            return True

        for x in checks:
            try:
                if not self.run_restriction(config=x.get('config'),
                                            name=x.get('name'),
                                            *args, **kwargs):
                    LOG.warning('Failed check for %s due to restriction %s',
                                name, x.get('name'))
                else:
                    LOG.info('Restriction ok %s: ', x.get('name'))
                    return True
            except Exception as e:
                LOG.exception(e)

        return False


    def start_plugins_group(self, ctx, plugin_group, block=False):
        """
        :param plugin group A list of ActionData objects
               to invoke start plugin using threadgroups.
        This need lot of tests, to assure context and self still
        available. or refactor.
        This will wait till all threads finish, so be carefull
        on handling to long the request until the async version
        is ready.

        Return number of executions
        """
        run_plugins = []
        runners = []
        for x in plugin_group:
            try:
                plug = self._get_and_check_plugin(x.name, action=x)
                if plug:
                    run_plugins.append((plug, x))
            except exceptions.CannotStartPlugin:
                pass
                        
        for plug_obj,data in run_plugins:
            # encapsulate in heat task ( why?... maybe it's usefull later)
            # but, anyways, clients are not ready for yield ops so...
            #this may block if check_for_status, we planned to have this check
            #in another service async, but.
            #runner.append(task)
                            
            # we could launch the tasks, and do a check_if_finished at the end, 
            # but if you need a task after the another it will break...
            # The thread will block until the action finish if it's blocking,
            # so it may impact the operation time on each sleep.
            # for poc is ok, but ....
            task = scheduler.TaskRunner(plug_obj.start, ctx=ctx, action=data, 
                                        block=block)
            self.thread_pool.add_thread(task.start)
        
        self.thread_pool.wait()
        return len(run_plugins)


    def _get_and_check_plugin(self, name, *args, **kwargs):
        """
        if kwargs contains omit_checks, won't apply
        restrictions.
        """
        try:
            plugin = self.get_plugin(name)()
            plugin.prepare_for_checks(*args, **kwargs)
            if not kwargs.get('omit_checks', False):
                if not self.can_execute(name, last_action=plugin.last_action,
                                        *args, **kwargs):
                    return None
            return plugin
        except Exception as e:
            #add pluginnotfound exception or something
            LOG.exception(e)
            raise exceptions.CannotStartPlugin(name=name)

        return None

    def start_plugin(self, name, *args, **kwargs):
        """
        Call start , check restrictions
        :name should be data.name
        :params args mandatory -> ctx and data

        if kwargs contains omit_checks, won't apply
        restrictions.
        """
        #TODO: add with reraise exception
        plugin = self._get_and_check_plugin(name, *args, **kwargs)
        if plugin:
           return plugin.start(*args, **kwargs)
        return None

    def check_plugin_name(self, name):
        return self.mgr[name]

    def get_plugin(self, name):
        try:
            return self.mgr[name].plugin
        except Exception:
            raise exceptions.NotFoundException('Plugin %s not found' % name)

    def run_restriction(self, name, *args, **kwargs):
        """ If false, restriction not passed."""
        restriction = self.get_restriction(name)
        if restriction:
            return restriction().can_execute(*args, **kwargs)
        return True

    def get_restriction(self, name):
        try:
            return self.restrictions[name].plugin
        except Exception as e:
            LOG.exception(e)
        return None


def get_plugin_handler():
    global CURRENT_HANDLER
    if not CURRENT_HANDLER:
        CURRENT_HANDLER = HandlerManager()
    return CURRENT_HANDLER
