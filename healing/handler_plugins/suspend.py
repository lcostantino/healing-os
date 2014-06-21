from healing.handler_plugins import base

from healing import exceptions
from healing.openstack.common import log as logging
from healing import utils


LOG = logging.getLogger(__name__)

class Suspend(base.HandlerPluginBase):
    """Suspend VM
    """
    DESCRIPTION = "Suspend/Resume VM"
    NAME = "suspend"

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
            config = action.action_meta_obj.get('data') or {}
            nova_action = config.get('action', 'suspend')
            if nova_action == 'resume':
                output = client.servers.resume(action.target_id)
            else:
                output = client.servers.suspend(action.target_id)

        except Exception as e:
            LOG.exception(e)
            self.error(action, message=e.message)
            return None
        
        self.finish(action, "")
        return self.current_action.id

    def can_execute(self, action, ctx=None):
        """
        :param action ActionData Obj
        move to parent?
        """
        return super(Suspend, self).can_execute(action, ctx=ctx)
