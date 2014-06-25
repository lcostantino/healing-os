import six

from healing import config
from healing import exceptions
from healing import utils
from healing.engine.alarms import alarm_base
from healing.openstack.common import log as logging
from healing.openstack.common import excutils
from healing.objects import alarm_track as alarm_obj

LOG = logging.getLogger(__name__)


class ExternalScriptAlarm(alarm_base.AlarmBase):

    """
    Dummy alarm that just register the AlarmTrack and expect
    an script or an external monitor system to call it.
    """
    ALARM_TYPE = 'external_script_alarm'

    def __init__(self, **kwargs):
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

class NotificationAlarm(ExternalScriptAlarm):
    ALARM_TYPE = 'notification_alarm'
