from healing.handler_plugins import base

from healing import exceptions
from healing.openstack.common import log as logging
from healing import utils

LOG = logging.getLogger(__name__)


class InstanceShow(base.HandlerPluginBase):
    """Output a nova show
    """
    DESCRIPTION = "Just output nova show for instance"
    NAME = "nova_show"
    
    def start(self, ctx, action, block=False):
        """ do something...  spawn thread?
            :param action ActionData Object
        """
        if not self.can_execute(action):
            self.register_action(action, discard=True)
            raise exceptions.ActionInProgress()

        self.register_action(action)
        try:
            client = utils.get_nova_client(ctx)
            output = client.servers.get(action.target_id)
        except Exception as e:
            LOG.exception(e)
            self.error(action, message=e.message)
            return None
        self.finish(action, str(output))
            
    def can_execute(self, action, ctx=None):
        return super(InstanceShow, self).can_execute(action, ctx=ctx)
