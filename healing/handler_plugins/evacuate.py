from healing.handler_plugins import base
from healing.objects import action as action_obj

from healing import exceptions
from healing.openstack.common import log as logging
from healing.openstack.common import timeutils
from healing import utils

from novaclient import client
import datetime

LOG = logging.getLogger(__name__)

class Evacuate(base.HandlerPluginBase):
    """evacuate host plugin.
    """
    DESCRIPTION = "evacuate"
    NAME = "evacuate"
    # if there's an action blahbla exeuted in this range,
    # ignore the request
    TIME_FOR_NEXT_ACTION = 10 * 60

    def start(self, ctx, data):
        """ do something...  spawn thread?
            :param data ActionData Object
        """
        if not self.can_execute(data):
            LOG.debug("Cannot execute. Other task in progress or time?")
            return False

        self._register_action(data)
        client = utils.get_nova_client(ctx)
        print client.servers.list()

        #do background? return id?
        print data
        return True

    def stop(self, data, error=False):
        #this will work if not in thread probably, if we change this
        #add the id to the data and context
        self.current_action.stop()
        self.current_action.save()
        LOG.debug("Task stopped")
        return False

    def can_execute(self, data):
        """
        :param data ActionData Obj
        """
        #use updated_at to move the logic to db instead of doing it in code
        # tHROW CannotExecuteExceptio and proper error in hook
        try:
            self.last_action = action_obj.Action.get_by_name_and_target(self.NAME,
                                                 data.target_resource)
        except exceptions.NotFoundException:
            LOG.debug("no action found. continue")
            return True

        if self.last_action.status == action_obj.ACTION_ERROR:
            LOG.debug("Action was in error state, continue")
            return True
        # nova should take care of the real status, won't be able to migrate/
        # evacuate twice even if running and job lost
        if not timeutils.is_older_than(self.last_action.created_at,
                                   self.TIME_FOR_NEXT_ACTION):
            LOG.debug("Action is not older than expected time and running")
            return False
        LOG.debug("Last Action for this handler: %s"  %  self.last_action.id)

        return True
