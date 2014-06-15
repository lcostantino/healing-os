from healing.handler_plugins import base

from healing import exceptions
from healing.openstack.common import jsonutils
from healing.openstack.common import log as logging
from healing import utils


LOG = logging.getLogger(__name__)

class Resize(base.HandlerPluginBase):
    """Resize VM
    """
    DESCRIPTION = "Resize to a bigger flavor"
    NAME = "resize"

    def start(self, ctx, action):
        """ do something...  spawn thread?
            :param action ActionData Object
        """
        if not self.can_execute(action):
            self.register_action(action, discard=True)
            raise exceptions.ActionInProgress()

        self.register_action(action)
        try:
            options = action.action_meta_obj.get('data') or {}
            flavor = options.get('flavor_id', '42')
            client = utils.get_nova_client(ctx)
            output = client.servers.resize(action.target_id, flavor=flavor)
        except Exception as e:
            LOG.exception(e)
            self.error(action, e.message)
            return None

        self.finish(action, str(output))
        return self.current_action.id

    def can_execute(self, action, ctx=None):
        """
        :param action ActionData Obj
        move to parent?
        """
        return super(Resize, self).can_execute(action, ctx=ctx)
