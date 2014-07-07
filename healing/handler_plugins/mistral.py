from healing.handler_plugins import base

from healing import exceptions
from healing.openstack.common import log as logging
from healing import utils

LOG = logging.getLogger(__name__)


class Mistral(base.HandlerPluginBase):
    """Trigger mistral workflow.

    Data format in action_meta is:
    {"workflow": "name", "task": "task", "params": {"admin_pass": "12123"}}
    """
    DESCRIPTION = "Run mistral workflow"
    NAME = "mistral"
    
    def _common_endpoints(self, ctx): 
        nova_url = utils.get_endpoint_url(ctx, 'compute')
        # remove project. should use urllib better..
        nova_url = "/".join(nova_url.split("/")[:-1])
        return {'nova_url': nova_url}
        
        
    def start(self, ctx, action, block=False):
        try:
            import mistralclient.api.client as client
            import mistralclient.api.executions as executions
        except:
            LOG.error("Mistral not installed")
            return

        if not self.can_execute(action):
            self.register_action(action, discard=True)
            raise exceptions.ActionInProgress()

        self.register_action(action)

        options = action.action_meta_obj.get('data') or {}
        workflow = options.get('workflow', None)
        task = options.get('task', None)
        params = options.get('params', {})
        if params.get('output'):
            params['output'] = '%s [%s]' % (params['output'],
                                            action.target_id)
        else:
            params['output'] = '[%s]' % action.target_id
            
        params['request_id'] = action.request_id
        
        if not params.get('instance_id'):
            params['instance_id'] = action.target_id
        if not params.get('project'):
            params['project'] = action.project_id
            
        params.update(self._common_endpoints(ctx))
        
        if not workflow or not task:
            LOG.warning('required parameters missing for mistral')
            self.stop(action, error=True)
            return
        try:
            client = client.Client(auth_token=ctx.token)
            execute = executions.ExecutionManager(client)
            output = execute.create(workflow, task, params)
        except Exception as e:
            LOG.exception(e)
            self.error(action, message=str(e))
            return None

        self.finish(action, str(output))
        return self.current_action.id
