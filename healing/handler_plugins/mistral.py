from healing.handler_plugins import base

from healing import exceptions
from healing.openstack.common import jsonutils
from healing.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class Mistral(base.HandlerPluginBase):
    """Trigger mistral workflow.

    Data format in action_meta is:
    {"workflow": "name", "task": "task", "params": {"admin_pass": "12123"}}
    """
    DESCRIPTION = "Run mistral workflow"
    NAME = "mistral"

    def start(self, ctx, action):
        try:
            import mistralclient.api.client as client
            import mistralclient.api.executions as executions
        except:
            raise
            LOG.error("Mistral not installed")
            return

        if not self.can_execute(action):
            self.register_action(action, discard=True)
            raise exceptions.ActionInProgress()

        self.register_action(action)
       
        options = action.action_meta_obj.get('data') or {}
        workflow = options.get('workflow', None)
        task = options.get('task', None)
        params = options.get('params', None)
        if not workflow or not task:
            LOG.warning('required parameters missing for mistral')
            self.stop(action, error=True)
            return
        try:
            client = client.Client()
            execute = executions.ExecutionManager(client)
            output = execute.create(workflow, task, params)
        except Exception as e:
            LOG.exception(e)
            self.error(action, message=str(e))
            return None

        self.finish(action, str(output))
        return self.current_action.id
