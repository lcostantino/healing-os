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
import abc
import six

from healing.openstack.common import log
from healing.openstack.common import jsonutils
from healing.objects import alarm_track as alarm_obj


LOG = log.getLogger(__name__)

STATE_OK = 'ok'
STATE_ALARM = 'alarm'
STATE_INSUFFICIENT = 'insufficient'

OK_HOOK = 'ok_actions'
ALARM_HOOK = 'alarm_actions'
INSUFFICIENT_HOOK = 'insufficient_data_actions'


CURRENT_HANDLER = None
"""
Handle AlarmObjs and ceilometer alarms. Always use this engine
to create AlarmObjs.

TODO: we can add a join table also for contract-alarm later. all the mess
is only forthe singleton alarm

I don't lke this, since we still need the obj to wrap,
but it's only for developers...
"""


class AlarmMetaClass(type):
    """Metaclass that allows tracking classes by alarm type."""
    AVAILABLE_ALARMS = {}

    def __init__(cls, names, bases, dict_):
        AlarmMetaClass.AVAILABLE_ALARMS[cls.ALARM_TYPE] = cls


@six.add_metaclass(AlarmMetaClass)
class AlarmBase(object):
    """ Some alarms will be unique , other's per VM, etc
        This work as a wrapper arund AlarmTrack objects
    """
    ALARM_TYPE = 'base'

    def __init__(self, ctx, remote_alarm_id=None,
                 contract_id=None, meter="dummy",
                 threshold=0, period=120, operator="eq",
                 query=None, alarm_object=None, evaluation_period=1,
                 statistic='avg', **kwargs):
        """
        You need to provide contract_id, meter, threshold, period and
        operator if it's a new object
        """
        self.ctx = ctx
        # additional data base on subclass
        self.options = kwargs or {}
        #this is filled in some specific cases on create/update
        self.extra_alarm_data = {}
        if alarm_object:
            self.alarm_track = alarm_object
            return
        # only update once if alarm_id not in place. Ex: (new alarm)
        # and only if values are set to avoid exceptions on field coercion
        # if will fail on save later if not properly set
        self.alarm_track = alarm_obj.AlarmTrack()
        self.contract_id = contract_id
        self.meter = meter
        self.alarm_id = remote_alarm_id
        self.period = period
        self.threshold = threshold
        self.statistic = statistic
        self.operator = operator
        self.evaluation_period = evaluation_period
        self.type = self.ALARM_TYPE

    # this could be done by __getattr__ and __setattr__ to proxy the object,
    # but.... make it explicity like this
    @property
    def alarm_track_id(self):
        return self.alarm_track.id

    @property
    def alarm_id(self):
        return self.alarm_track.alarm_id

    @alarm_id.setter
    def alarm_id(self, val):
        self.alarm_track.alarm_id = val

    @property
    def type(self):
        return self.alarm_track.type

    @type.setter
    def type(self, val):
        self.alarm_track.type = val

    @property
    def contract_id(self):
        return self.alarm_track.contract_id

    @contract_id.setter
    def contract_id(self, val):
        self.alarm_track.contract_id = val

    @property
    def meter(self):
        return self.alarm_track.meter

    @meter.setter
    def meter(self, val):
        self.alarm_track.meter = val

    @property
    def threshold(self):
        return self.alarm_track.threshold

    @threshold.setter
    def threshold(self, val):
        self.alarm_track.threshold = val

    @property
    def operator(self):
        return self.alarm_track.operator

    @operator.setter
    def operator(self, val):
        self.alarm_track.operator = val

    @property
    def period(self):
        return self.alarm_track.period

    @period.setter
    def period(self, val):
        self.alarm_track.period = val

    @property
    def statistic(self):
        return self.alarm_track.statistic

    @statistic.setter
    def statistic(self, val):
        self.alarm_track.statistic = val

    @property
    def evaluation_period(self):
        return self.alarm_track.evaluation_period

    @evaluation_period.setter
    def evaluation_period(self, val):
        self.alarm_track.evaluation_period = val

    @property
    def query(self):
        # TODO MUST: Add a json field that do this into fields.py
        try:
            return jsonutils.loads(self.alarm_track.query)
        except:
            return []

    @query.setter
    def query(self, val):
        self.alarm_track.query = jsonutils.dumps(val)

    @abc.abstractmethod
    def create(self):
        pass

    def set_from_dict(self, update_dict):
        for x in alarm_obj.AlarmTrack.fields.keys():
            present = update_dict.get(x)
            if present:
                #to avoid change_fields being modified
                setattr(self, x, present)

    @abc.abstractmethod
    def update(self):
        pass

    @abc.abstractmethod
    def delete(self):
        pass

    def is_active(self):
        return True

    def get_extra_alarm_data(self):
        return self.extra_alarm_data

    def affected_resources(self, group_by='resource_id',
                           period=0, query=None,
                           start_date=None, end_date=None,
                           aggregates=None, delta_seconds=None,
                           meter=None,
                           result_process=None):
        pass

    def set_default_alarm_hook(self):
        pass

    def set_default_ok_hook(self):
        pass

    def set_default_insufficient_hook(self):
        pass

    def set_ok_hook_url(self, url):
        pass

    def set_alarm_hook_url(self, url):
        pass

    def set_insufficient_hook_url(self, url):
        pass

    def get_hooks(self):
        pass
