import six

from healing import config
from healing import exceptions
from healing import utils
from healing.engine.alarms import alarm_base
from healing.openstack.common import log as logging
from healing.openstack.common import excutils
from healing.objects import alarm_track as alarm_obj

from ceilometerclient import exc as cl_exception

LOG = logging.getLogger(__name__)


class CeilometerAlarm(alarm_base.AlarmBase):
    """
    Options Params can have: base_alarm_url , ok_actions, alarm_actions ,
    insufficient_data urls, project
    or a standard one will be created in
    CONF.alarm_host_url/?status=[ok,alarm,insufficient]
    Subclasses my add contract_id for instance or whatever is required,
    but the alarm_id is enough to search the proper AlarmTrack

    It operate over saved alarmtrack objects, so should not be directly
    used.
    """
    client = None
    ALARM_TYPE = 'ceilometer_alarm'

    def __init__(self, **kwargs):
        self.hooks = {}
        super(CeilometerAlarm, self).__init__(**kwargs)

    def _get_client(self):
        if not self.client:
            self.client = utils.get_ceilometer_client(self.ctx)
        return self.client

    def _build_default_hook(self, params):
        url = self.options.get('base_alarm_url',
                               None) or config.CONF.api.alarm_handler_url
        params['source'] = 'ceilometer'
        return '?'.join((url, six.moves.urllib_parse.urlencode(params)))

    def set_default_alarm_hook(self, params=None):
        params = params or {}
        params['status'] = alarm_base.STATE_ALARM
        self.hooks[alarm_base.ALARM_HOOK] = [self._build_default_hook(params)]

    def set_default_ok_hook(self, params=None):
        params = params or {}
        params['status'] = alarm_base.STATE_OK
        self.hooks[alarm_base.OK_HOOK] = [self._build_default_hook(params)]

    def set_default_insufficient_hook(self, params=None):
        params = params or {}
        params['status'] = alarm_base.STATE_INSUFFICIENT
        self.hooks[alarm_base.INSUFFICIENT_HOOK] = \
                                [self._build_default_hook(params)]

    def set_ok_hook_url(self, url):
        self.hooks[alarm_base.OK_HOOK] = url

    def set_alarm_hook_url(self, url):
        self.hooks[alarm_base.ALARM_HOOK] = url

    def set_insufficient_hook_url(self, url):
        self.hooks[alarm_base.INSUFFICIENT_HOOK] = url

    def add_query(self, field, value, operator="eq", field_type=''):
        query = self.query or []
        # to avoid 2 calls to json till field is ready
        query.append(utils.build_ceilometer_query(field, operator, value, field_type))
        self.query = query

    def build_alarm_fields(self):
        repeat = self.options.get('repeat', False)
        project = self.options.get('project_id', None)
        fields = {'meter_name': self.meter,
                  'period': self.period,
                  'comparison_operator': self.operator,
                  'name': self.alarm_track_id or self.alarm_id,
                  'threshold': self.threshold,
                  'repeat_actions': repeat,
                  'type': 'threshold'}
        if self.statistic:
            fields['statistic'] = self.statistic
        if self.evaluation_period:
            fields['evaluation_period'] = self.evaluation_period
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

    def affected_resources(self, group_by='resource_id',
                           period=0, query=None,
                           start_date=None, end_date=None,
                           aggregates=None, delta_seconds=None,
                           meter=None,
                           result_process=None):

        """
        Fetch statics based on period and same threshold.
        this is usefull mostly for singleton alarms or
        tenant resource based alarms.
        You may monitor tenant/project for cpu statics, but
        in this case, you won't get the exact resource if there's
        one or a combination of samples.
        For other types of alarm where resource is unique, you
        can fetch it straight from the contract model.

        :param period Period of time. This will
                      split the statistics in periods so, check if it's
                      what you expect.
        :param query something like [{'field': 'start', 'type': '', 'value':
                                      '2014-06-03T00:53:00', 'op': 'eq'}]
        :param start_date Samples started on datetime.
                          ( if not set will be
                            current_time - delta or Alarm_Period - x)
        :param end_date Samples finished on - if not set will be current_time
        :param delta_seconds If end_data start_date is None, will substract
                             seconds from current_date==end_date
        :param meter Meter name or current alarm meter name. The param is here
                     to do combination queries in future alarms

        :param result_process if it's a function invoke it on results

        The result is returned as it's. Must implement a generic converter.

        """

        try:
            client = self._get_client()
            meter = meter or self.meter
            if not start_date:
                delta_seconds = delta_seconds or (self.period * self.evaluation_period) 

            res = utils.get_ceilometer_statistics(client, meter=meter, period=period, 
                                                  query=query,
                                                  start_date=start_date, end_date=end_date,
                                                  delta_seconds = delta_seconds,
                                                  group_by=group_by,
                                                  aggregates=aggregates or [])
            if result_process:
                return result_process()(self, res)
            return res

        except Exception as e:
            LOG.exception(e)
            raise # cannotgetresourceseceptin
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

    def __init__(self, **kwargs):
        self.unique_alarm_obj = None
        super(HostDownUniqueAlarm, self).__init__(**kwargs)

    def get_unique_alarm(self, refresh=False):
        if not self.unique_alarm_obj or refresh:
            try:
                self.unique_alarm_obj = alarm_obj.AlarmTrack.get_by_type(
                                                            self.ALARM_TYPE)
            except exceptions.NotFoundException:
                self.unique_alarm_obj = None
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
                if not self.hooks.get(alarm_base.ALARM_HOOK):
                    self.set_default_alarm_hook()
                super(HostDownUniqueAlarm, self).create()
                external_created = True
            else:
                LOG.debug('Creaint oject only')
                self.alarm_id = self.unique_alarm_obj.alarm_id
            self.alarm_track.save()
        except exceptions.ExternalAlarmAlreadyExists as e:
            LOG.exception(e)
            raise
        except Exception as e:
            LOG.exception(e)
            with excutils.save_and_reraise_exception():
                self.alarm_track.delete()
                if external_created:
                    super(HostDownUniqueAlarm, self).delete()
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


class ResourceAlarm(CeilometerAlarm):

    """
    Resource could be project or resurce
    Since we get kwargs as options, you must initiate it with

    ResourceAlarm(ctx, project_id=XXX or resource_id=XXXXX)

    If you need more queries, just call add_custom_query or prepare
    the queries on constructor
    """
    ALARM_TYPE = 'ceilometer_resource_alarm'

    def create(self):
        """
        # Check if already in DB if it's the first one, create it.?
        search by type
        """

        try:
            external_created = False
            if (not self.options.get('project_id') and
                    not self.options.get('resource_id')):
                raise Exception('missing parameter project_id or resource_id')

            self.alarm_track.create()

            if not self.hooks.get(alarm_base.ALARM_HOOK):
                self.set_default_alarm_hook({'contract_id':
                                             self.alarm_track.contract_id})

            if self.options.get('project_id'):
                self.add_query('project_id', self.options.get('project_id'))
            if self.options.get('resource_id'):
                self.add_query('resource_id', self.options.get('resource_id'))
            # DO A WITH with autodelete if fail.. or move external_created
            # to parent...
            super(ResourceAlarm, self).create()
            external_created = True
            self.alarm_track.save()
        except exceptions.ExternalAlarmAlreadyExists as e:
            raise
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


class ExternalResourceAlarm(CeilometerAlarm):

    """
    Build the record from an already existing Ceilometer Alarm.
    We need the user to call update on alarm change or we can
    update ourselves on affected_resources call but need to do
    1 more rest query on each call..

    We only handle alarms that have resource_id as filter
    """
    ALARM_TYPE = 'ceilometer_external_resource'

    def __init__(self, **kwargs):
        super(ExternalResourceAlarm, self).__init__(**kwargs)
        self.alarm_id = self.options.get('alarm_id', self.alarm_id)

    def _clone_alarm_data(self):
        # We only handle alarms with resource_id and
        # project id. Even that will work for tenant alarms without
        # resource, this may get outdated on affect_resources queries
        if not self.alarm_id:
            raise exceptions.InvalidDataException('Missing alarm_id')
        client = self._get_client()
        try:
            alarm = client.alarms.get(self.alarm_id)
        except:
            raise exceptions.NotFoundException('External alarm not found')
        self.period = alarm.rule.get('period')
        self.evaluation_period = alarm.rule.get('evaluation_period')
        self.threshold = alarm.rule.get('threshold')
        self.operator = alarm.rule.get('comparison_operator')
        self.statistic = alarm.rule.get('statistic')
        self.meter = alarm.rule.get('meter_name')
        self.query = alarm.rule.get('query') or []
        self.extra_alarm_data['project_id'] = alarm.project_id
        for x in self.query:
            if x.get('field') == 'resource_id':
                self.extra_alarm_data['resource_id'] = x.get('value')
                return
        raise exceptions.InvalidDataException('Missing resource_id in query')

    def create(self):
        try:
            self._clone_alarm_data()
            self.alarm_track.create()
        except exceptions.HealingException as e:
            LOG.exception(e)
            raise
        except Exception as e:
            LOG.exception(e)
            raise exceptions.AlarmCreateOrUpdateException()

    def update(self):
        try:
            self._clone_alarm_data()
            self.alarm_track.update()
        except exceptions.HealingException as e:
            LOG.exception(e)
            raise
        except Exception as e:
            LOG.exception(e)
            raise exceptions.AlarmCreateOrUpdateException()

    def delete(self):
        try:
            self.alarm_track.delete()
        except Exception as e:
            LOG.exception(e)
            raise exceptions.AlarmCreateOrUpdateException()


class ExternalScriptAlarm(alarm_base.AlarmBase):

    """
    Dummy alarm that just register the AlarmTrack and expect
    an script or an external monitor system to call it.
    """
    ALARM_TYPE = 'external_script_alarm'
    hooks = {}

    def __init__(self, **kwargs):
        self.unique_alarm_obj = None
        super(ExternalScriptAlarm, self).__init__(**kwargs)

    def create(self):
        try:
            self.alarm_track.create()
        except Exception as e:
            LOG.exception(e)
            raise exceptions.AlarmCreateOrUpdateException()

    def update(self):
        pass

    def delete(self):
        try:
            self.alarm_track.delete()
        except Exception as e:
            LOG.exception(e)
            raise exceptions.AlarmCreateOrUpdateException()

