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

import time

from healing.openstack.common import log as logging
from healing.openstack.common import timeutils
from healing.engine.alarms import manager as alarm_manager
from healing.engine.alarms import ceilometer_alarms as cel_alarms
from healing.objects.sla_contract import SLAContract as sla_contract
from healing.objects.failure_track import FailureTrack as failure_track
from healing.handler_plugins.action_data import ActionData
from healing.handler_manager import get_plugin_handler as handler_manager
from healing import utils

LOG = logging.getLogger(__name__)


class SLAContractEngine():

    HOST_DOWN_ALARM_TYPE = cel_alarms.HostDownUniqueAlarm.ALARM_TYPE
    HOST_DOWN_ALARM_METER = 'services.compute_host.down'
    HOST_DOWN_ALARM_OP = 'eq'

    def create(self, ctx, contract_dict, period):
        contract_created = sla_contract.from_dict(contract_dict).create()

        self._create_alarm(ctx, contract_created.id, period)
        return contract_created.to_dict()

    def update(self, ctx, contract_dict, period):
        contract_saved = sla_contract.from_dict(contract_dict).save()

        self._create_alarm(ctx, contract_saved.id, period)
        return contract_saved.to_dict()

    def delete(self, ctx, contract_id, period):
        self._delete_alarm(ctx, contract_id)
        sla_contract.delete(id)

    def get(self, contract_id):
        contract = sla_contract.get_by_contract_id(contract_id)
        return contract.to_dict()

    def get_all(self):
        contracts = sla_contract.get_all()
        contract_dicts = [contract.to_dict() for contract in contracts]
        return contract_dicts

    @classmethod
    def _delete_alarm(ctx, contract_id):
        alarm = alarm_manager.get_by_contract_id(ctx, contract_id)
        alarm.delete()

    @classmethod
    def _create_alarm(cls, ctx, contract_id, period):
        alarm = alarm_manager.alarm_build_by_type(ctx,
                                    cls.HOST_DOWN_ALARM_TYPE,
                                    remote_alarm_id=None,
                                    contract_id=contract_id,
                                    meter=cls.HOST_DOWN_ALARM_METER,
                                    threshold=1,
                                    period=period,
                                    operator=cls.HOST_DOWN_ALARM_OP,
                                    query=None,
                                    alarm_object=None)
        alarm.create()


class SLAAlarmingEngine():

    def alert(self, ctx, alarm_id, source):
        alarm = alarm_manager.get_by_id(ctx, alarm_id)
        contract = sla_contract.get_by_contract_id(alarm.contract_id)
        project = contract.project_id
        hosts = alarm.affected_resources(period=3, delta_seconds=120)
        print(str(hosts))
        if not hosts:
            LOG.error('Not resources associated to the alarm')

        vms = []
        client = utils.get_nova_client(ctx)

        self._track_failure(timeutils.utcnow(), alarm_id, str(hosts))

        for host in hosts:
            vms.append(utils.get_nova_vms(client, tenant_id=project, host=host))

        for vm in vms:
            action = ActionData('evacuate', source=source, target_resource=vm.id)
            plugin = handler_manager.get_plugin('evacuate')
            plugin.start(ctx, action)

    @classmethod
    def _track_failure(time, alarm_id, data):
        failure = failure_track()
        failure.time = time
        failure.alarm_id = alarm_id
        failure.data = data

        failure.create()

    @classmethod
    def track_failure_get_all(self):
        failure = failure_track()
        failures = [failure.to_dict() for failure in failure_track.get_all()]
        return failures