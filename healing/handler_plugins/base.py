import abc


from healing import exceptions
from healing.openstack.common import timeutils
from healing.openstack.common import log as logging
from healing.objects import action as action_obj

LOG = logging.getLogger(__name__)


class ActionData(object):
    def __init__(self, name, target_resource, source='custom',
                 data=None, headers=None):
        self.name = name
        self.target_resource = target_resource
        self.source = source
        self.action_meta = {'headers': headers,
                            'data': data}

    def __str__(self):
        return "ActionData {0}|{1}|{2}|{3}".format(self.name, self.source,
                                                   self.target_resource,
                                                   self.action_meta)


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

    @abc.abstractmethod
    def start(self, ctx, data):
        """start action for ActionDataObj.
           :param ctx current Context
           :param data ActionData Object
           Can raise ActionInProgress
           Return action id
        """

    @abc.abstractmethod
    def stop(self, data):
        """stop action for data."""

    def abort(self):
        pass

    def get_current_action(self):
        """ Get current registered action object."""
        return self.current_action

    def can_execute(self, data):
        """can execute check. depends on plugin.
           should call parent and implement custom logic
           :param data ActionData object
        """
        try:
            self.last_action = action_obj.Action.get_by_name_and_target(
                                                        self.NAME,
                                                        data.target_resource)
        except exceptions.NotFoundException:
            LOG.debug("No action found for %s. continue" % self.NAME)
            return True

        if self.last_action.status == action_obj.ACTION_ERROR:
            LOG.debug("Action was in error state %s continue" %
                      self.last_action.id)
            return True
        # maybe moved to db query... depends..
        if not timeutils.is_older_than(self.last_action.created_at,
                                       self.TIME_FOR_NEXT_ACTION):
            LOG.debug("Action %s is not older than expected time and running"
                      % self.last_action.id)
            return False
        LOG.debug("Last Action for this handler: %s" % self.last_action.id)
        return True

    def _register_action(self, data, status='started'):
        #todo throw propoer exeception
        #TODO: move to objects
        action = action_obj.Action()
        action.name = self.NAME
        action.action_meta_obj = data.action_meta or {}
        action.target_id = data.target_resource
        action.status = action_obj.ACTION_STARTED
        self.current_action = action.create()
#get_name mandatory?
