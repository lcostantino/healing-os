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
"""Load plugins
"""
import abc
from healing import config
from healing import exceptions
from healing import utils
from healing.openstack.common import log
from healing.openstack.common import jsonutils
from healing.openstack.common import excutils
from healing.objects import alarm_track as alarm_obj

from ceilometerclient import exc as cl_exception

LOG = log.getLogger(__name__)


CURRENT_HANDLER = None
"""
Handle AlarmObjs and ceilometer alarms. Always use this engine
to create AlarmObjs.

TODO: we can add a join table also for contract-alarm later. all the mess
is only forthe singleton alarm

I don't lke this, since we still need the obj to wrap,
but it's only for developers...
"""


class AlarmBase(object):
    """ Some alarms will be unique , other's per VM, etc
        This work as a wrapper arund AlarmTrack objects
    """

    def __init__(self, ctx, remote_alarm_id=None,
                 contract_id=None, meter=None,
                 threshold=None, period=None, operator=None,
                 query=None, alarm_object=None, **kwargs):

        self.ctx = ctx
        # additional data base on subclass
        self.options = kwargs or {}
        if alarm_object:
            self.alarm_track = alarm_object
            return
        # only update once if alarm_id not in place. Ex: (new alarm)
        self.alarm_track = alarm_obj.AlarmTrack()
        self.contract_id = contract_id
        self.meter = meter
        self.alarm_id = remote_alarm_id
        self.period = period
        self.threshold = threshold
        self.operator = operator
        self.type = self.ALARM_TYPE

    @classmethod
    def get_all_by_type(cls, ctx, kwargs=None):
        try:
            obj = alarm_obj.AlarmTrack.get_all_by_type(cls.ALARM_TYPE) or []
            return [cls(ctx=ctx, alarm_object=x, kwargs=kwargs) for x in obj]
        except Exception as e:
            LOG.exception(e)
            return None

    @classmethod
    def get_by_contract_id(cls, ctx, contract_id, kwargs=None):
        try:
            obj = alarm_obj.AlarmTrack.get_by_contract_id(contract_id)
            return cls(ctx=ctx, alarm_object=obj, kwargs=kwargs)
        except Exception as e:
            LOG.exception(e)
            return None

    @classmethod
    def get_by_id(cls, ctx, alarm_track_id, kwargs=None):
        try:
            obj = alarm_obj.AlarmTrack.get_by_id(alarm_track_id)
            return cls(ctx=ctx, alarm_object=obj, kwargs=kwargs)
        except Exception as e:
            LOG.exception(e)
            return None

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

    @abc.abstractmethod
    def update(self):
        pass

    @abc.abstractmethod
    def delete(self):
        pass

    def is_active(self):
        return True

    # TODO: change name
    def who_trigger_it(self):
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
    
    
# TODO: add with context to reduce repeated code of create/update/etc
class CeilometerAlarm(AlarmBase):
    """
    Options Params can have: base_alarm_url , ok_actions, alarm_actions ,
    insufficient_data urls, project
    or a standard one will be created in
    CONF.alarm_host_url/?status=[ok,alarm,insufficient]
    Subclasses my add contract_id for instance or whatever is required,
    but the alarm_id is enough to search the proper AlarmTrack
    """
    client = None
    ALARM_TYPE = 'ceilometer_alarm'
    hooks = {}

    def _get_client(self):
        if not self.client:
            self.client = utils.get_ceilometer_client(self.ctx)
        return self.client

    def set_default_alarm_hook(self):
        url = self.options.get('base_alarm_url',
                               None) or config.CONF.api.alarm_handler_url
        self.hooks['alarm_actions'] = [url + "?status=alarm"]

    def set_default_ok_hook(self):
        url = self.options.get('base_alarm_url',
                               None) or config.CONF.api.alarm_handler_url
        self.hooks['ok_actions'] = [url + "?status=ok"]

    def set_default_insufficient_hook(self):
        url = self.options.get('base_alarm_url',
                               None) or config.CONF.api.alarm_handler_url
        self.hooks['insufficient_data_actions'] = [url +
                                                   "?status=insufficient"]

    def set_ok_hook_url(self, url):
        self.hooks['ok_actions'] = url

    def set_alarm_hook_url(self, url):
        self.hooks['alarm_actions'] = url

    def set_insufficient_hook_url(self, url):
        self.hooks['insufficient_data_actions'] = url
        
    def add_query(self, field, value, operator="eq", field_type=''):
        query = self.query or []
        # to avoid 2 calls to json till field is ready
        query.append({'field': field, 'op': operator, 
                      'value': value, 'type': field_type})
        self.query = query
                      
    def build_alarm_fields(self):
        repeat = self.options.get('repeat', False)
        project = self.options.get('project_id', None)
        fields = {'meter_name': self.meter,
                  'period': self.period,
                  'comparison_operator': self.operator,
                  'name': self.alarm_id or self.alarm_track_id,
                  'threshold': self.threshold,
                  'repeat_actions': repeat,
                  'type': 'threshold'}
        if project:
            fields['project_id'] = project
            
        fields.update(self.hooks)
        if self.query:
            # TODO: build query base on ceilometer expectation
            fields['threshold_rule'] = {'query': self.query}
        """
        [{'field': 'resource', 'type': '', 'value': '2', 'op': 'eq'}]
        """
        return fields

    def create(self):
        """
        Will fail if the name already exist. Each subclass
        should form a name with resource / project / id, etc
        """
        try:
            client = self._get_client()
            new_alarm = client.alarms.create(**self.build_alarm_fields())
            self.alarm_id = new_alarm.alarm_id
            return self.alarm_track
        # Cacth? HTTPConflict
        except cl_exception.HTTPConflict as exc:
            LOG.exception(exc)
            raise exceptions.ExternalAlarmAlreadyExists()

    def update(self):
        client = self._get_client()
        client.alarms.update(alarm_id=self.alarm_id,
                             **self.build_alarm_fields())
        return self.alarm_track

    def delete(self):
        try:
            client = self._get_client()
            client.alarms.delete(alarm_id=self.alarm_id)
        except cl_exception.HTTPNotFound:
            return

    def is_active(self):
        pass

    def who_trigger_it(self):
        pass


class HostDownUniqueAlarm(CeilometerAlarm):

    """ This kind of alarm is 'singleton'. We only associate different
        contract ids to same alarm.
        It also override who_trigger_it , because we dont' recieve the
        target resource.
        To delete this alarm, only one existence of this alarm id should
        be in alarm tracker.

        Unique means the same alarm, even that there can be lot of
        AlarmTracks with the same id
    """
    ALARM_TYPE = 'host_down_unique'
    unique_alarm_obj = None

    def get_unique_alarm(self, refresh=False):
        if not self.unique_alarm_obj or refresh:
            try:
                self.unique_alarm_obj = None
                self.unique_alarm_obj = alarm_obj.AlarmTrack.get_by_type(
                                                                self.ALARM_TYPE)
            except exceptions.NotFoundException:
                pass

        return self.unique_alarm_obj

    def _is_first_alarm(self):
        #probably check against ceilometer?
        return self.get_unique_alarm() is None

    def _something_changed(self):
        """
        The singleton alarm is repeated everywhere, but one update
        should not update every time on every contract.
        """
        return not self.unique_alarm_obj.same_values(self.alarm_track)

    def create(self):
        """
        # Check if already in DB if it's the first one, create it.?
        search by type
        """
        try:

            external_created = False
            # TODO: if duplicated, raise or we expect the caller
            # to handle that?
            first_alarm = self._is_first_alarm()
            self.alarm_track.create()
            # TODO: id must be unique, so double query but assure
            # % of success
            # other way would be to use random, or use
            # some id . but they can be created outside
            # we may use contract id only if it 1<->1
            if first_alarm:
                LOG.debug("Creating unique external alarm")
                if not self.hooks.get('alarm_actions'):
                    self.set_default_alarm_hook()
                super(HostDownUniqueAlarm, self).create()
                external_created = True
            else:
                LOG.debug('Creaint oject only')
                self.alarm_id = self.unique_alarm_obj.alarm_id
            self.alarm_track.save()
        except exceptions.ExternalAlarmAlreadyExists as e:
            LOG.exception(e)
            # TODO: maybe raise?
            return
        except Exception as e:
            LOG.exception(e)
            with excutils.save_and_reraise_exception():
                self.alarm_track.delete()
            # add with rereaise
                if external_created:
                    super(HostDownUniqueAlarm, self).delete()
            # TODO: add with reraise exception
            raise exceptions.AlarmCreateOrUpdateException()

    def update(self):
        try:
            if not self.get_unique_alarm():
                raise Exception("Cannot update a singleton alarm"
                                "not already created - parent")
            if self._something_changed():
                LOG.debug("The alarm changed, do the update now.")
                super(HostDownUniqueAlarm, self).update()

            self.alarm_track.save()
            return self.alarm_track
        except Exception as e:
            LOG.exception(e)
            raise exceptions.AlarmCreateOrUpdateException()

    def delete(self):
        try:
            if self.alarm_track and self.alarm_track_id:
                self.alarm_track.delete()

            if not self.get_unique_alarm(refresh=True):
                LOG.warning('Last AlarmTrack, removing ceilometer alarm')
                super(HostDownUniqueAlarm, self).delete()
        except Exception as e:
            LOG.exception(e)
            raise exceptions.AlarmCreateOrUpdateException()

# falta un create_alarm o algo en ase al type invoque la clase

class ResourceAlarm(CeilometerAlarm):

    """
    Resource could be project or resurce
    Since we get kwargs as options, you must initiate it with
    
    ResourceAlarm(ctx, project_id=XXX or resource_id=XXXXX)
    
    If you need more queries, just call add_custom_query or prepare
    the queries on constructor
    """
    ALARM_TYPE = 'resource_generic_alarm'
    def create(self):
        """
        # Check if already in DB if it's the first one, create it.?
        search by type
        """
        try:
            external_created = False
            if not self.options.get('project_id') and not self.options.get('resource_id'):
                raise Exception('missing parameter project_id or resource_id')
            
            self.alarm_track.create()
            
            if not self.hooks.get('alarm_actions'):
                self.set_default_alarm_hook()
            
            if self.options.get('project_id'):
                self.add_query('project_id', self.options.get('project_id'))
            else:
                self.add_query('resource_id', self.options.get('resource_id'))
            # DO A WITH with autodelete if fail.. or move external_created
            # to parent...
            super(ResourceAlarm, self).create()
            external_created = True
            self.alarm_track.save()
        except exceptions.ExternalAlarmAlreadyExists as e:
            LOG.exception(e)
            # TODO: maybe raise?
            return
        except Exception as e:
            LOG.exception(e)
            with excutils.save_and_reraise_exception():
                self.alarm_track.delete()
            # add with rereaise
                if external_created:
                    super(ResourceAlarm, self).delete()
            # TODO: add with reraise exception
            raise exceptions.AlarmCreateOrUpdateException()

    def update(self):
        try:
            self.alarm_track.save()
            return self.alarm_track
        except Exception as e:
            LOG.exception(e)
            raise exceptions.AlarmCreateOrUpdateException()

    def delete(self):
        try:
            if self.alarm_track and self.alarm_track_id:
                self.alarm_track.delete()
            super(ResourceAlarm, self).delete()
        except Exception as e:
            LOG.exception(e)
            raise exceptions.AlarmCreateOrUpdateException()


def get_alarm_type():
   pass