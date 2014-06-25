import abc

from healing.openstack.common import timeutils
from healing.openstack.common import log as logging

LOG = logging.getLogger(__name__)

class RestrictionBase(object):
    """Check if a plugin handler (that use ActionObjects)
       can be executed or not base on config and data
       It's tied to action object model,be warned..

       IF one plugin return True, we accept the execution. so order matters?
    """

    __metaclass__ = abc.ABCMeta
    DESCRIPTION = 'base_restriction'
    NAME = 'base_restriction'
    CFG_PARAMS = {}

    @abc.abstractmethod
    def can_execute(self, config, last_action=None, ctx=None, action=None, **kwargs):
        """Evaluate if can be executed
           :param last_action Last recorded execution for this action (ActionObj)
           :param ctx current Context
           :param action Actionaction Object
           :param restriction_cconfig from yaml, depends on plugin
           Can raise ActionInProgress
           Return action id
        """

class TimeIntervalRestriction(RestrictionBase):
    """If last action execution happened in 'interval seconds', then deny the
       execution of this plugin."""

    NAME = 'TimeInterval'
    CFG_PARAMS = {'interval': 60*10}

    def can_execute(self, config, last_action=None, ctx=None, action=None, **kwargs):
        if not last_action:
            return True
        interval = int(config.get('interval', self.CFG_PARAMS['interval']))

        updated_at = last_action.updated_at
        if updated_at and not timeutils.is_older_than(last_action.updated_at, interval):
            LOG.debug("Action %s is not older than expected interval"
                      % last_action.id)
            return False

        if not timeutils.is_older_than(last_action.created_at, interval):
            LOG.debug("Action %s is not older than expected interval"
                      % last_action.id)
            return False

        return True


class ActionStatusRestriction(RestrictionBase):
    CFG_PARAMS = {'status': 'error'}

    def can_execute(self, config, last_action=None, ctx=None, action=None, **kwargs):
        if not last_action:
            return True
        return (last_action.status == config.get('status', self.CFG_PARAMS['status']))

