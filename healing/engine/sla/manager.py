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

from healing.openstack.common import log as logging
import healing.engine.alarms.manager as manager
import healing.engine.alarms.ceilometer_alarms as cel_alarms
from healing.objects import sla_contract as objects

LOG = logging.getLogger(__name__)


class SLAEngine():

    HOST_DOWN_ALARM_TYPE = cel_alarms.HostDownUniqueAlarm.ALARM_TYPE
    HOST_DOWN_ALARM_METER = 'services.compute_host.down'
    HOST_DOWN_ALARM_OP = 'eq'

    def create(self, ctx, contract_dict, period):
        contract = objects.SLAContract()
        contract.from_dict(contract_dict)
        contract_created = contract.create()

        self._create_alarm(ctx, contract_created.id, period)
        return contract_created.to_dict()

    def update(self, ctx, contract_dict, period):
        contract = objects.SLAContract()
        contract.from_dict(contract_dict)
        contract_saved = contract.save()

        self._create_alarm(ctx, contract_saved.id, period)
        return contract_saved.to_dict()

    def delete(self, ctx, contract_id, period):
        self._delete_alarm(ctx, contract_id)
        objects.SLAContract.delete(id)

    def get(self, contract_id):
        contract = objects.SLAContract.get_by_contract_id(contract_id)
        return contract.to_dict()

    def get_all(self):
        contracts = objects.SLAContract.get_all()
        contract_dicts = [contract.to_dict() for contract in contracts]
        return contract_dicts

    @classmethod
    def _delete_alarm(ctx, contract_id):
        manager.get_by_contract_id(ctx, contract_id)

    @classmethod
    def _create_alarm(cls, ctx, contract_id, period):
        manager.alarm_build_by_type(ctx, cls.HOST_DOWN_ALARM_TYPE,
                                    remote_alarm_id=None,
                                    contract_id=contract_id,
                                    meter=cls.HOST_DOWN_ALARM_METER,
                                    threshold=1,
                                    period=period,
                                    operator=cls.HOST_DOWN_ALARM_OP,
                                    query=None,
                                    alarm_object=None)



