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

    Data format in action_meta is:

           'evacuate_vm': True  if evacuating a vm in target_resource,
           if not the entire host will be evacuated
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
            raise exceptions.ActionInProgress()

        self._register_action(data)
        client = utils.get_nova_client(ctx)
        print client.servers.list()
        return self.current_action.id
        #do background? return id?

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
        move to parent?
        """
        return super(Evacuate, self).can_execute(data)
