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

from healing.openstack.common import jsonutils
from healing.openstack.common import log as logging
from healing.openstack.common import timeutils
from healing import exceptions as exc
from healing.engine.alarms import manager as alarm_manager
from healing.engine.alarms import ceilometer_alarms as cel_alarms
from healing.objects.sla_contract import SLAContract as sla_contract
from healing.objects.failure_track import FailureTrack as failure_track
from healing.objects.alarm_track import AlarmTrack
from healing.handler_plugins.action_data import ActionData
from healing.handler_manager import get_plugin_handler as handler_manager
from healing import utils

LOG = logging.getLogger(__name__)

SLA_TYPES = {'HOST_DOWN': {'alarm': cel_alarms.HostDownUniqueAlarm.ALARM_TYPE,
                           'options': {'meter': 'services.compute_host.down',
                                       'operator': 'eq',
                                       'threshold': 1,
                                       'repeatable': True},
                           'override': False},
             'RESOURCE': {'alarm': cel_alarms.ResourceAlarm.ALARM_TYPE,
                          'override': True,
                          'options': None}
            }

def validate_contract_info(contract_dict, update=False):
    ctype = contract_dict.get('type')
    if not update or ctype:
        if not ctype in SLA_TYPES:
            raise exc.InvalidDataException('Invalid or missing type')
    try:
        if not update or contract_dict.get('action'):
            handler_manager().check_plugin_name(contract_dict.get('action'))
    except Exception as e:
        LOG.exception(e)
        raise exc.InvalidDataException('Action not valid or available')

class SLAContractEngine():
    HOST_DOWN_ALARM_TYPE = cel_alarms.HostDownUniqueAlarm.ALARM_TYPE
    HOST_DOWN_ALARM_METER = 'services.compute_host.down'
    HOST_DOWN_ALARM_OP = 'eq'

    def create(self, ctx, contract_dict):
        validate_contract_info(contract_dict)
        # WARN: IF PROJECT_ID NULL AND RESOURCE_ID NULL DO NOt ALLOw
        # TO CONTRACTS FOR 'ALL' on the same ALARM tyPE
        contract_created = sla_contract.from_dict(contract_dict).create()
        try:
            self._create_alarm(ctx, contract_created,
                               contract_dict.get('alarm_data'))
        except Exception:
            contract_created.delete(contract_created.id)
            raise
        return contract_created.to_dict()

    def update(self, ctx, contract_dict):
        validate_contract_info(contract_dict, update=True)
        contract_saved = sla_contract.from_dict(contract_dict).save()
        self._update_alarm(ctx, contract_saved, contract_dict.get('alarm_data'))
        return contract_saved.to_dict()

    def delete(self, ctx, contract_id):
        self._delete_alarm(ctx, contract_id)
        sla_contract.delete(contract_id)

    def get(self, contract_id):
        contract = sla_contract.get_by_contract_id(contract_id)
        return contract.to_dict()

    def get_all(self):
        contracts = sla_contract.get_all()
        contract_dicts = [contract.to_dict() for contract in contracts]
        return contract_dicts

    def _delete_alarm(self, ctx, contract_id):
        alarm = alarm_manager.get_by_contract_id(ctx, contract_id)

        if alarm:
            alarm.delete()

    def _parse_alarm_opts(self, ctx, alarm_type, alarm_data, update=False):
        al_type = SLA_TYPES.get(alarm_type)
        additional_info = {}
        if alarm_data:
            try:
                additional_info = jsonutils.loads(alarm_data)
            except Exception as e:
                LOG.error(e)
                pass
        if not additional_info and not update:
            # to avoid writing the same values
            if not al_type.get('override', False):
                additional_info.update(al_type.get('options'))
        additional_info.pop('id', None)
        return (al_type.get('alarm'), additional_info)

    def _update_alarm(self, ctx, contract_obj, alarm_data):
        # do we want this here? or just call alarm update api?
        # change client to pass alarm_data
        (al_type, additional_info) = self._parse_alarm_opts(ctx,
                                                            contract_obj.type,
                                                            alarm_data,
                                                            update=True)
        alarm = alarm_manager.get_by_contract_id(ctx, contract_obj.id)
        if alarm and additional_info:
            alarm.set_from_dict(additional_info)
            alarm.update()

    def _create_alarm(self, ctx, contract_obj, alarm_data):
        (al_type, additional_info) = self._parse_alarm_opts(ctx,
                                                            contract_obj.type,
                                                            alarm_data)
        alarm = alarm_manager.alarm_build_by_type(ctx,
                                    al_type,
                                    remote_alarm_id=None,
                                    contract_id=contract_obj.id,
                                    alarm_object=None,
                                    **additional_info)
        alarm.create()


class SLAAlarmingEngine():

    def alert(self, ctx, alarm_id, source):
        alarm = alarm_manager.get_by_alarm_id(ctx, alarm_id)
        if not alarm:
            raise exc.NotFoundException('No Alarm found with id %s' % alarm_id)

        contract_ids = AlarmTrack.get_contracts_by_alarm_id(alarm_id)
        if not contract_ids:
            return

        contracts = [sla_contract.get_by_contract_id(contract_id)
                     for contract_id in contract_ids]
        projects = [contract.project_id for contract in contracts]
        projects.sort(reverse=True)

        hosts = alarm.affected_resources(period=3, delta_seconds=120)
        if not hosts:
            LOG.error('Not resources associated to the alarm')
            return

        failure_id = self._track_failure(timeutils.utcnow(), alarm_id,
                                         str(hosts))

        vms = []
        client = utils.get_nova_client(ctx)
        if not client:
            raise Exception('Error retrieving nova client')

        for host in hosts:
            for project in projects:
                vms.append(utils.get_nova_vms(client, tenant_id=project,
                                              host=host))

        for vm in vms:
            action = ActionData('evacuate', source=source,
                                request_id=failure_id,
                                target_resource=vm.id,)
            plugin = handler_manager.get_plugin('evacuate')
            plugin.start(ctx, action)

    @classmethod
    def _track_failure(time_utc, alarm_id, data):
        failure = failure_track()
        failure.time = time_utc
        failure.alarm_id = alarm_id
        failure.data = data
        failure.create()
        return failure.id

    @classmethod
    def track_failure_get_all(self):
        failure = failure_track()
        failures = [failure.to_dict() for failure in failure_track.get_all()]
        return failures
