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

# TODO: add with context to reduce repeated code of create/update/etc


class CeilometerAlarm(alarm_base.AlarmBase):
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

    def _build_default_hook(self, params):
        url = self.options.get('base_alarm_url',
                               None) or config.CONF.api.alarm_handler_url
        return '?'.join((url, six.moves.urllib_parse.urlencode(params)))

    def set_default_alarm_hook(self, params=None):
        params = params or {}
        params['status'] = alarm_base.STATE_ALARM
        self.hooks[alarm_base.ALARM_HOOK] = self._build_default_hook(params)

    def set_default_ok_hook(self, params=None):
        params = params or {}
        params['status'] = alarm_base.STATE_OK
        self.hooks[alarm_base.OK_HOOK] = self._build_default_hook(params)

    def set_default_insufficient_hook(self, params=None):
        params = params or {}
        params['status'] = alarm_base.STATE_INSUFFICIENT
        self.hooks[alarm_base.INSUFFICIENT_HOOK] = \
                                self._build_default_hook(params)

    def set_ok_hook_url(self, url):
        self.hooks[alarm_base.OK_HOOK] = url

    def set_alarm_hook_url(self, url):
        self.hooks[alarm_base.ALARM_HOOK] = url

    def set_insufficient_hook_url(self, url):
        self.hooks[alarm_base.INSUFFICIENT_HOOK] = url

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
            if (not self.options.get('project_id') and
                    not self.options.get('resource_id')):
                raise Exception('missing parameter project_id or resource_id')

            self.alarm_track.create()

            if not self.hooks.get(alarm_base.ALARM_HOOK):
                self.set_default_alarm_hook({'contract_id':
                                             self.alarm_tract.contract_id})

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
