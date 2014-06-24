#
# Copyright 2012 eNovance <licensing@enovance.com>
# Copyright 2012 Red Hat, Inc
#
# Author: Julien Danjou <julien@danjou.info>
# Author: Eoghan Glynn <eglynn@redhat.com>
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

from oslo.config import cfg

from ceilometer.compute import plugin
from ceilometer.compute.pollsters import util
from ceilometer import sample
from ceilometer import nova_client
from ceilometer.openstack.common import timeutils
from ceilometer.compute.virt import inspector

class InstancePollster(plugin.ComputePollster):

    @staticmethod
    def get_samples(manager, cache, resources):
        for instance in resources:
            yield util.make_sample_from_instance(
                instance,
                name='instance',
                type=sample.TYPE_GAUGE,
                unit='instance',
                volume=1,
            )


class InstanceFlavorPollster(plugin.ComputePollster):

    @staticmethod
    def get_samples(manager, cache, resources):
        for instance in resources:
            yield util.make_sample_from_instance(
                instance,
                # Use the "meter name + variable" syntax
                name='instance:%s' %
                instance.flavor['name'],
                type=sample.TYPE_GAUGE,
                unit='instance',
                volume=1,
            )

class VMErrorStatusPollster(plugin.ComputePollster):

    def _get_vms(self, manager):
        vms = nova_client.Client().instance_get_all_by_host(cfg.CONF.host)
        for vm in vms:
            instance_name = util.instance_name(vm)
            state = manager.inspector.inspect_state(instance_name)
            if state.state == inspector.PAUSED:
                yield vm

    def _iter_vms(self, manager, cache):
        """Iterate over all services based on service_type."""
        if 'vms' not in cache:
            cache['vms'] = list(self._get_vms(manager))
        return iter(cache['vms'])

    def get_samples(self, manager, cache, resources=[]):
        for vm in self._iter_vms(manager, cache):
            yield sample.Sample(
                name='services.vm.error',
                type=sample.TYPE_GAUGE,
                unit='error',
                volume=1,
                project_id=None,
                user_id=None,
                resource_id=vm.id,
                timestamp=timeutils.isotime(),
                resource_metadata={}
            )