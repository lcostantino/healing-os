# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
#
# Author: Julien Danjou <julien@danjou.info>
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
"""Retrieve Compute Host Service status
"""

from __future__ import absolute_import

import ceilometer.nova_client as nova_client

from ceilometer.openstack.common import timeutils
from ceilometer import plugin
from ceilometer import sample


class _Base(plugin.PollsterBase):

    def _is_down(self, service):
        if service.state == 'down' and service.status == 'enabled':
            return True
        return False
    
        
    def _get_services(self, service_type=None, down=False):
        services = nova_client.Client().services_get_all()
        for service in services:
            # to support None for all services
            if not service_type or service.binary == service_type:
                if not down or ( down and self._is_down(service) ):
                    yield service

    def _iter_services(self, cache, service_type='nova-compute', down=True):
        """Iterate over all services based on service_type."""
        if 'services' not in cache:
            cache['services'] = list(self._get_services(service_type, down))
        return iter(cache['services'])

    
class ServicesComputeHostPollster(_Base):

    def get_samples(self, manager, cache, resources=[]):
        print "Getting samples?"
        for service in self._iter_services(cache, 'nova-compute', down=True):
            yield sample.Sample(
                name='services.compute_host.down',
                type=sample.TYPE_GAUGE,
                unit='down',
                volume=1,
                project_id=None,
                user_id=None,
                resource_id=service.host,
                timestamp=timeutils.isotime(),
                resource_metadata={
                    'host': service.host,
                    'status': service.status,
                }
            )
