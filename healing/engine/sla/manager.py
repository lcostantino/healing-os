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
from healing.engine.alarms import filters
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
    if not update and ctype == SLA_TYPES['RESOURCE']['alarm']:
        if not ctype.get('project_id') and not ctype.get('resoure_id'):
            raise exc.InvalidActionException('Project ID or Resource ID '
                                             'required for Resource Alarm')

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
                                    resource_id=contract_obj.resource_id,
                                    project_id=contract_obj.project_id,
                                    **additional_info)
        alarm.create()


class SLAAlarmingEngine():
    def _process_resource_alarm(self, ctx, alarm, contract, source):
        """ Untested."""
        resource = [contract.resource_id]
        project = contract.project_id
        if not resource:
            resources = [project]

        failure_id = self._track_failure(timeutils.utcnow(), alarm.alarm_id,
                                         str(resources))
        if not contract.resource_id:
            time_frame = (alarm.period * alarm.evaluation_period) #* 2
            resources = alarm.affected_resources(period=alarm.period,
                                    delta_seconds=time_frame,
                                    result_process=filters.FormatResources)
        if not resources:
            LOG.warning('No resource found on ResourceAlarm %s'
                        % alarm.alarm_id)
            return ""

        for x in resources:
            actions.append(ActionData(name=contract.action,
                                      source=source,
                                      request_id=failure_id,
                                      target_resource=x))
        if actions:
            handler_manager().start_plugins_group(ctx, actions)
        # WARN: we may want to change state alarm now if it's tenant
        # scoped, so it get repeated?

    def _process_host_down_alarm(self, ctx, alarm, contracts, source):

        time_frame = (alarm.period * alarm.evaluation_period) #* 2
        # we use the cache to avoid hosts processed in the last time
        # can be dne with filter periods, but we may loose
        # hosts that we failed to process for other reaons
        resources = alarm.affected_resources(period=alarm.period,
                            delta_seconds=time_frame,
                            result_process=filters.FormatResources)
        if resources:
            resources = [x for x in resources if
                         not utils.get_cache_value(x)]
            LOG.debug('Resources after cache check %s' % str(resources))

        if not resources:
            LOG.warning('no affected resources associated to the alarm '
                        'in time frame seconds: %s' % time_frame)
            return

        failure_id = self._track_failure(timeutils.utcnow(), alarm.alarm_id,
                                         str(resources))
        client = utils.get_nova_client(ctx)
        vms_by_tenant = {}
        # WARN; if fails and filtered by statistics we may never act
        # again on host we think we did...
        for host in resources:
            try:
                # any particular state? Running only?
                vms_by_tenant.update(utils.get_nova_vms(client, host=host))
            except Exception as e:
                LOG.exception(e)
                continue
        # specific contracts
        spec_contract_actions = {}
        generic_contract = False
        for x in contracts:
            if x.project_id is not None:
                spec_contract_actions[x.project_id] = (x.action)
            else:
                generic_contract = x.action
        actions = []
        for prj,action in spec_contract_actions.iteritems():
            vms = [x.id for x in vms_by_tenant.get(prj, {})]
            for vm in vms:
                actions.append(ActionData(name=action, source=source,
                                    request_id=failure_id,
                                    target_resource=vm['id']))
            vms_by_tenant.pop(prj, None)
        # may need refactor, need to process twice
        if generic_contract:
            for prj,vms in vms_by_tenant.iteritems():
                for vm in vms:
                    actions.append(ActionData(name=generic_contract,
                                              source=source,
                                              request_id=failure_id,
                                              target_resource=vm['id']))
        for x in resources:
            utils.set_cache_value(x)

        if actions:
            handler_manager().start_plugins_group(ctx, actions)

    def alert(self, ctx, alarm_id, source):
        alarm = alarm_manager.get_by_alarm_id(ctx, alarm_id)
        contract_ids = AlarmTrack.get_contracts_by_alarm_id(alarm_id)

        contracts = []
        for x in contract_ids:
            try:
                contracts.append(sla_contract.get_by_contract_id(x))
            except exc.NotFoundException:
                pass
        if not contracts:
            raise exc.NotFoundException('No contracts or alarms found')

        if alarm.type == SLA_TYPES['HOST_DOWN']['alarm']:
            return self._process_host_down_alarm(ctx, alarm, contracts, source)
        else:
            return self._process_resource_alarm(ctx, alarm, contracts, source)

    def _track_failure(self, time_utc, alarm_id, data):
        failure = failure_track()
        failure.time = time_utc
        failure.alarm_id = alarm_id
        failure.data = data
        failure.create()
        return failure.id

    @classmethod
    def track_failure_get_all(cls):
        failures = [failure.to_dict() for failure in failure_track.get_all()]
        return failures
