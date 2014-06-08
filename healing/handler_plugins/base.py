import abc


from healing import exceptions
from healing.openstack.common import timeutils
from healing.openstack.common import log as logging
from healing.objects import action as action_obj

LOG = logging.getLogger(__name__)


class HandlerPluginBase(object):
    """Base class for handlers plugins
    """

    __metaclass__ = abc.ABCMeta
    DESCRIPTION = 'base'
    NAME = 'base'
    SCHEMA = 'define'
    TIME_FOR_NEXT_ACTION = 0

    def __init__(self):
        self.current_action = None
        self._last_action = None
        
    @property
    def last_action(self):
        return self._last_action
    
    @abc.abstractmethod
    def start(self, ctx, data):
        """start action for ActionDataObj.
           :param ctx current Context
           :param data ActionData Object
           Can raise ActionInProgress
           Return action id
        """

    @abc.abstractmethod
    def stop(self, data, error=False):
        """stop action for data."""

    def abort(self):
        pass

    def get_current_action(self):
        """ Get current registered action object."""
        return self.current_action

    def prepare_for_checks(self, data, ctx=None):
        """ Fill minimal data for restrictions to avoid having 
            plugin handler dependency here.."""
        try:
            self._last_action = action_obj.Action.get_by_name_and_target(
                                                        self.NAME,
                                                        data.target_resource)
        except exceptions.NotFoundException:
            LOG.info("No action found for %s. continue" % self.NAME)
        
    def can_execute(self, data, ctx=None):
        """can execute check. depends on plugin.
           should call parent and implement custom logic
           :param data ActionData object
        """
        return True
    
    def register_action(self, data, status=action_obj.ACTION_STARTED):
        #todo throw propoer exeception
        #TODO: move to objects
        action = action_obj.Action()
        action.name = self.NAME
        action.action_meta_obj = data.action_meta or {}
        action.target_id = data.target_resource
        action.status = action_obj.ACTION_STARTED
        action.request_id = data.request_id
        action.create()
        self.current_action = action

#get_name mandatory?
