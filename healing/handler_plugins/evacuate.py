from healing.handler_plugins import base

from healing import exceptions
from healing.openstack.common import log as logging
from healing.openstack.common import jsonutils
from healing import utils


LOG = logging.getLogger(__name__)

class Evacuate(base.HandlerPluginBase):
    """evacuate VM plugin.

    Data format in action_meta is:
        'evacuate_host': True  if evacuating the entire host
    """
    DESCRIPTION = "Evacuate VM (shared storage)"
    NAME = "evacuate"

    def start(self, ctx, action):
        """ do something...  spawn thread?
            :param action Action Object
            shared_storage?
        """
        if not self.can_execute(action):
            self.register_action(action, discard=True)
            raise exceptions.ActionInProgress()
        
        self.register_action(action)
        try:
            config = jsonutils.loads(action.action_meta.get('data') or {})
            client = utils.get_nova_client(ctx)
            host = config.get('dest_host', None)
            shared = config.get('shared_storage', True)
            output = client.servers.evacuate(server=action.target_id,
                                            host=host, on_shared_storage=shared)
            output = str(output)
        except Exception as e:
            LOG.exception(e)
            self.error(action, message=str(e))
            return None

        self.finish(action, message=output)
        return action.id


    def can_execute(self, action, ctx=None):
        """
        :param action Actionaction Obj
        move to parent?
        """
        return super(Evacuate, self).can_execute(action, ctx=ctx)
