import abc
from healing.db import api as db_api

from healing.openstack.common import jsonutils
from healing.objects import action as action_obj

class HandlerPluginBase(object):
    """Base class for handlers plugins
    """

    __metaclass__ = abc.ABCMeta
    DESCRIPTION = 'base'
    NAME = 'base'
    SCHEMA = 'define'


    def __init__(self):
        self.current_action = None

    @abc.abstractmethod
    def start(self, ctx, data):
        """start action for data."""

    @abc.abstractmethod
    def stop(self, data):
        """stop action for data."""

    def abort(self):
        pass

    def get_current_action(self):
        return self.current_action

    @abc.abstractmethod
    def can_execute(self, data):
        """can execute check. depends on plugin."""

    def _register_action(self, data, status='started'):
        #todo throw propoer exeception
        #TODO: move to objects
        action = action_obj.Action()
        action.name = self.NAME
        action.action_meta_obj = data.get('action_meta', {})
        action.target_id = data['target_resource']
        action.status = action_obj.ACTION_STARTED
        self.current_action = action.create()
#get_name mandatory?
