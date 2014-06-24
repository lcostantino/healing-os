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

from healing.openstack.common import log as logging
from healing import utils

LOG = logging.getLogger(__name__)
PERIOD = 60


class CeilometerStatistics():

    def __init__(self):
        self.instance_stats = None
        self.cpu_stats = None

    def prepare(self, ctx, project_id=None, start_date=None,
                         end_date=None, resource_id=None):

        aggr_count = [{'func': 'count'}, ]
        aggr_min = [{'func': 'min'}, ]
        self.instance_stats = self._get_statistics(ctx, 'instance', start_date,
                                                   end_date, project_id,
                                                   resource_id, aggr_count)
        self.cpu_stats = self._get_statistics(ctx, 'cpu', start_date, end_date,
                                         project_id, resource_id, aggr_min)

        utils.validate_not_empty(instance_stats=self.instance_stats)
        utils.validate_not_empty(cpu_stats=self.cpu_stats)

    def get_resource_period(self, resource_id, start_date, end_date):
        min_date = end_date.replace(tzinfo=None)
        max_date = start_date.replace(tzinfo=None)
        for stat in self.instance_stats:
            if stat.groupby['resource_id'] == resource_id:
                period_start = parse(stat.period_start).replace(tzinfo=None)
                if period_start < min_date:
                    min_date = period_start
                if period_start > max_date:
                    max_date = period_start
        return (max_date - min_date).seconds

    def resource_unavailability(self, resource_id, start_time, to_time):
        min_time = to_time.replace(tzinfo=None)
        from_time = start_time.replace(tzinfo=None)
        for stat in self.cpu_stats:
            period_start = parse(stat.period_start).replace(tzinfo=None)
            if from_time < period_start < min_time and int(stat.min) > 0 and \
                            stat.groupby['resource_id'] == resource_id:
                min_time = period_start

        return (min_time - from_time).seconds

    def _get_statistics(self, ctx, meter, start_date, end_date, project_id,
                       resource_id=None, aggregates=None):
        client = utils.get_ceilometer_client(ctx)
        group_by = ['resource_id', 'project_id']
        query = self._get_filter_query(project_id, resource_id)

        return utils.get_ceilometer_statistics(client, group_by=group_by,
                              period=PERIOD, start_date=start_date,
                              end_date=end_date, aggregates=aggregates,
                              meter=meter, query=query)

    def _get_filter_query(self, project_id=None, resource_id=None):
        query = []
        if project_id:
            query.append(utils.build_ceilometer_query(field='project_id',
                                                      operator='eq',
                                                      value=project_id))
        if resource_id:
            query.append(utils.build_ceilometer_query(field='resource_id',
                                                      operator='eq',
                                                      value=resource_id))
        return query

    def get_vms_per_project(self, project_id):
        vms = []
        for stat in self.instance_stats:
            if stat.groupby['project_id'] == project_id:
                vms.append(stat.groupby['resource_id'])

        return vms
