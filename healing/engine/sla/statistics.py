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

from healing import utils
from healing.openstack.common import log as logging
from healing.engine.sla.manager import SLAAlarmingEngine
from healing.engine.sla.statistics_api import StatisticsAPI
from healing.objects.action import Action

LOG = logging.getLogger(__name__)


class SLAStatisticsEngine():

    PERIOD = 60

    def __init__(self):
        self.stats = StatisticsAPI.get_impl()

    def get_statistics(self, stat_type, **args):
        utils.validate_not_empty(stat_type=stat_type)
        return getattr(self, 'get_%s' % stat_type)(**args)

    def get_availability(self, ctx, project_id, start_date, end_date,
                         resource_id=None):
        utils.validate_not_empty(start_date=start_date)
        utils.validate_not_empty(end_date=end_date)
        utils.validate_not_empty(project_id=project_id)

        self.stats.prepare(ctx, project_id, start_date, end_date, resource_id)

        alarms = SLAAlarmingEngine.track_failure_get_all(start_date, end_date)
        actions = {}
        for alarm in alarms:
            actions[alarm['id']] = Action.get_all_by_request_id(alarm['id'])

        if resource_id:
            unavailable_time = self._resource_unavailability(resource_id,
                                                             alarms,
                                                             actions,
                                                             end_date)
            period = self.stats.get_resource_period(resource_id, start_date,
                                                    end_date)

            if period == 0:
                raise Exception('Not valid period detected')
            else:
                return 100 - (unavailable_time * 100 / period)
        else:
            utils.validate_not_empty(project_id=project_id)

            total_unavailable_time = 0
            total_period = 0
            vms = self.stats.get_vms_per_project(project_id)
            for vm in vms:
                single_unavailable_time = self._resource_unavailability(vm,
                                                                alarms,
                                                                actions,
                                                                end_date)
                total_unavailable_time += single_unavailable_time
                single_period = self.stats.get_resource_period(vm,start_date,
                                                               end_date)
                total_period += single_period

            return 100 - (total_unavailable_time * 100 / total_period)

    def get_max_unavailable_period(self, ctx, project_id, start_date, end_date,
                                   resource_id):
        utils.validate_not_empty(start_date=start_date)
        utils.validate_not_empty(end_date=end_date)
        utils.validate_not_empty(project_id=project_id)
        utils.validate_not_empty(resource_id=resource_id)

        self.stats.prepare(ctx, project_id, start_date, end_date, resource_id)

        alarms = SLAAlarmingEngine.track_failure_get_all(start_date, end_date)
        actions = {}
        for alarm in alarms:
            actions[alarm['id']] = Action.get_all_by_request_id(alarm['id'])

        periods = self._resource_unavailability_periods(resource_id, alarms,
                                                        actions, end_date)

        if periods:
            periods.sort(reverse=True)
        else:
            raise Exception('No unavailable periods for resource %s' %
                            str(resource_id))

        return periods[0]



    #TODO: Just consider the machines with cpu > 0 before the failure
    def _resource_unavailability(self, resource_id, alarms, actions, to_date):
        unavailable_time = 0
        for alarm in alarms:
            for action in actions[alarm['id']]:
                if action.target_id == resource_id:
                    unavailable_time += self.stats.resource_unavailability(
                                                                resource_id,
                                                                alarm['created_at'],
                                                                to_date)
        return unavailable_time

    #TODO: Just consider the machines with cpu > 0 before the failure
    def _resource_unavailability_periods(self, resource_id, alarms, actions,
                                         to_date):
        unavailable_periods = []
        for alarm in alarms:
            for action in actions[alarm['id']]:
                if action.target_id == resource_id:
                    unavailable_periods.append(self.stats.resource_unavailability(
                                                                resource_id,
                                                                alarm['created_at'],
                                                                to_date))
        return unavailable_periods
