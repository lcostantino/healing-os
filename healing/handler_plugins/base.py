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
    def start(self, ctx, action, block=False):
        """start action for ActionDataObj.
           :param ctx current Context
           :param action ActionData Object
           Can raise ActionInProgress
           Return action id
        """
        
    def error(self, action, message=None):
        self.stop(action, action_obj.ACTION_ERROR,  message)
    
    def discard(self, action, message=None):
        self.stop(action, action_obj.ACTION_DISCARDED,  message)
        
    def finish(self, action, message):
        self.stop(action, action_obj.ACTION_FINISHED,  message)

    def block_until_finish(self, action, ctx=None):
        pass
    
    def stop(self, action, status, message=None):
        """stop action.."""
        #this will work if not in thread probably, if we change this
        #add the id to the action and context
        action.status = status
        action.output = message
        action.save()
        LOG.debug("Task stopped")

    def abort(self):
        pass

    def get_current_action(self):
        """ Get current registered action object."""
        return self.current_action

    def prepare_for_checks(self, action, ctx=None):
        """ Fill minimal action for restrictions to avoid having 
            plugin handler dependency here.."""
        try:
            self._last_action = action_obj.Action.get_by_name_and_target(
                                                        self.NAME,
                                                        action.target_id,
                                                        ignore_status='pending')
        except exceptions.NotFoundException:
            LOG.info("No action found for %s. continue" % self.NAME)
        
    def can_execute(self, action, ctx=None):
        """can execute check. depends on plugin.
           should call parent and implement custom logic
           :param action ActionData object
        """
        return True
    
    def register_action(self, action, status=action_obj.ACTION_STARTED,
                        discard=False):
        self.current_action = action
        if discard:
            status = action_obj.ACTION_DISCARDED
        action.status = status
        action.save()

#get_name mandatory?
