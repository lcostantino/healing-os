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

from dateutil.parser import parse

from healing.openstack.common import jsonutils
from healing.openstack.common import log as logging
from healing.openstack.common import timeutils
from healing.engine.sla.manager import SLAAlarmingEngine
from healing.objects.action import Action
from healing import utils

LOG = logging.getLogger(__name__)

PERIOD = 60
STATISTICS = 'statistics'
GROUP_BY = 'groupby'
RESOURCE_ID = 'resource_id'
PROJECT_ID = 'project_id'
MIN = 'min'
COUNT = 'count'
INSTANCE = 'instance'
CPU = 'cpu'


def validate_not_empty(**kwargs):
    for name, value in kwargs.iteritems():
        if value is None or (isinstance(value, str) and len(value) == 0):
            raise Exception("%s cannot be None" % name)


class SLAStatisticsEngine():

    PERIOD = 60

    def get_actions_number(self, type=None, project_id=None, start=None,
                           end=None):
        return 1

    def get_availability(self, ctx, project_id=None, start_date=None,
                         end_date=None, resource_id=None):
        print("#################get_availability#################")
        print(locals())

        if not start_date or not end_date or not project_id:
            #TODO: use proper exception
            raise Exception('Missing information to calculate availability')

        aggr_count = [{'func': COUNT}, ]
        aggr_min = [{'func': MIN}, ]
        instance_stats = self._get_statistics(ctx, INSTANCE, start_date,
                                              end_date, project_id, resource_id,
                                              aggr_count)
        cpu_stats = self._get_statistics(ctx, CPU, start_date, end_date,
                                         project_id, resource_id, aggr_min)

        validate_not_empty(instance_stats=instance_stats)
        validate_not_empty(cpu_stats=cpu_stats)

        alarms = SLAAlarmingEngine.track_failure_get_all(start_date, end_date)
        print('####alarms: %s' % str(alarms))
        actions = {}
        for alarm in alarms:
            actions[alarm['id']] = Action.get_all_by_request_id(alarm['id'])
        print('####actions: %s' % str(actions))

        if resource_id:
            unavailable_time = self._per_resource_availability(resource_id,
                                                               alarms,
                                                               actions,
                                                               cpu_stats,
                                                               end_date)
            period = self._get_resource_period(resource_id, instance_stats,
                                                  start_date, end_date)

            return unavailable_time * 100 / period
        else:
            if project_id is None:
                #TODO: raise proper exception
                raise Exception('Project ID not provided')

            total_unavailable_time = 0
            total_period = 0
            for vm in self._get_vms_per_project(instance_stats, project_id):
                total_unavailable_time += self._per_resource_availability(
                                                                vm,
                                                                alarms,
                                                                actions,
                                                                cpu_stats,
                                                                end_date)
                total_period += self._get_resource_period(vm, instance_stats,
                                                        start_date, end_date)

            print('unavailable_time: %s' % str(total_unavailable_time))
            print('period: %s' % str(total_period))
            return total_unavailable_time * 100 / total_period



    #TODO: Move to ceilometer based statistics calcualtions
    def _get_resource_period(self, resource_id, instance_stats, start_date,
                               end_date):
        print("#################_get_resource_period#################")
        #print(locals())

        min_date = end_date.replace(tzinfo=None)
        max_date = start_date.replace(tzinfo=None)
        for stat in instance_stats:
            if stat.groupby[RESOURCE_ID] == resource_id:
                period_start = parse(stat.period_start).replace(tzinfo=None)
                if period_start < min_date:
                    min_date = period_start
                if period_start > max_date:
                    max_date = period_start
        return (max_date - min_date).seconds

    #TODO: Move to ceilometer based statistics calcualtions
    def _per_resource_availability(self, resource_id, alarms, actions,
                                  cpu_stats, to_date):
        unavailable_time = 0
        for alarm in alarms:
            for action in actions[alarm['id']]:
                if action.target_id == resource_id:
                    unavailable_time += self._get_unavailavility_time(
                                                                cpu_stats,
                                                                resource_id,
                                                                alarm['time'],
                                                                to_date)
        return unavailable_time

    #TODO: Just consider the machines with cpu > 0 before the failure
    #TODO: Move to ceilometer based statistics calcualtions
    def _get_unavailavility_time(self, cpu_stats, resource_id, start_time,
                                 to_time):
        print("#################_get_unavailavility_time#################")
        #print(locals())

        min_time = to_time.replace(tzinfo=None)
        from_time = start_time.replace(tzinfo=None)
        for stat in cpu_stats:
            period_start = parse(stat.period_start).replace(tzinfo=None)
            if from_time < period_start < min_time and int(stat.min) > 0 and \
                            stat.groupby['resource_id'] == resource_id:
                min_time = period_start

        return (min_time - from_time).seconds

    #TODO: Move to ceilometer based statistics calcualtions
    def _get_statistics(self, ctx, meter, start_date, end_date, project_id,
                       resource_id=None, aggregates=None):
        print("#################_get_statistics#################")
        #print(locals())

        group_by = [RESOURCE_ID, PROJECT_ID]
        stats = self._get_ceilometer_statistics(ctx, meter, start_date,
                                                   end_date, PERIOD, aggregates,
                                                   group_by)
        return self._filter_statistics(stats, project_id, resource_id)

    #TODO: Move to ceilometer based statistics calcualtions
    def _get_ceilometer_statistics(self, ctx, meter, start_date, end_date,
                                  period, aggregates, group_by):
        print("#################_get_ceilometer_statistics#################")
        #print(locals())

        client = utils.get_ceilometer_client(ctx)
        stats = utils.get_ceilometer_statistics(client, group_by=group_by,
                              period=period, start_date=start_date,
                              end_date=end_date, aggregates=aggregates,
                              meter=meter)
        return stats

    #TODO: Move to ceilometer based statistics calcualtions
    #TODO: make this through a ceilometer query
    def _filter_statistics(self, statistics, project_id=None, resource_id=None):

        print("#################_filter_statistics#################")
        #print(locals())

        validate_not_empty(statistics=statistics)

        filtered_stats = []
        for stat in statistics:
            match = True
            if project_id:
                match = match and stat.groupby[PROJECT_ID] == project_id
            if resource_id:
                match = match and stat.groupby[RESOURCE_ID] == resource_id
            if match:
                filtered_stats.append(stat)

        return filtered_stats

    #TODO: stats should come filtered and grouped by red and proj
    def _get_vms_per_project(self, instance_stats, project_id):
        print("#################_get_vms_per_project#################")
        #print(locals())

        validate_not_empty(instance_stats=instance_stats)
        vms = []
        for stat in instance_stats:
            if stat.groupby[PROJECT_ID] == project_id:
                vms.append(stat.groupby[RESOURCE_ID])

        return vms


