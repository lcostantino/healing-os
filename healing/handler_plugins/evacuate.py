from healing.handler_plugins import base

from healing import exceptions
from healing.openstack.common import log as logging
from healing.openstack.common import jsonutils
from healing import utils
import time

LOG = logging.getLogger(__name__)

class Evacuate(base.HandlerPluginBase):
    """evacuate VM plugin.

    Data format in action_meta is:
        'evacuate_host': True  if evacuating the entire host
    """
    DESCRIPTION = "Evacuate VM (shared storage)"
    NAME = "evacuate"

    def start(self, ctx, action, block=False):
        """ do something...  spawn thread?
            :param action Action Object
            shared_storage?
        """
        if not self.can_execute(action):
            self.register_action(action, discard=True)
            raise exceptions.ActionInProgress()

        self.register_action(action)
        try:
            config = action.action_meta_obj.get('data') or {}
            self.client = utils.get_nova_client(ctx)
            host = config.get('dest_host', None)
            shared = config.get('shared_storage', True)
            if not block:
                block = config.get('block', False)
            output = self.client.servers.evacuate(server=action.target_id,
                                            host=host, on_shared_storage=shared)
            output = str(output)
        except Exception as e:
            LOG.exception(e)
            self.error(action, message=str(e))
            return None
        
        if block:
            self.block_until_finish(action, ctx)
        else:
            self.finish(action, message=output)
        
        return action.id

    def block_until_finish(self, action, ctx=None):
        """ Block the execution until the server is ACTIVE or ERROR. 
            Only for POC..., this block the thread..
            Ideally we can ask for instance action based on the 
            request_id but it's not returned by novaclient.... BP?
            Another option is to wait for the notification.
        """
        for x in range(0,10):
            try:
                server = self.client.servers.get(server=action.target_id)
                if getattr(server, 'OS-EXT-STS:task_state')  is None:
                    vm_state = getattr(server, 'OS-EXT-STS:vm_state')
                    if vm_state.lower() == 'active':
                        self.finish(action, server.status)
                    if vm_state.lower() == 'error':
                        self.error(action, message=server.status)
            except Exception as e:
                LOG.exception(e)
                pass
            
            time.sleep(5)
        
        pass
    

    def can_execute(self, action, ctx=None):
        """
        :param action Actionaction Obj
        move to parent?
        """
        return super(Evacuate, self).can_execute(action, ctx=ctx)
