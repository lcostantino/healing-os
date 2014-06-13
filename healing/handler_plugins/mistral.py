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

    def start(self, ctx, data):
        try:
            import mistralclient.api.client as client
            import mistralclient.api.executions as executions
        except:
            raise
            LOG.error("Mistral not installed")
            return

        if not self.can_execute(data):
            raise exceptions.ActionInProgress()

        self.register_action(data)
        options = jsonutils.loads(data.action_meta.get('data') or {})
        workflow = options.get('workflow', None)
        task = options.get('task', None)
        params = options.get('params', None)
        if not workflow or not task:
            LOG.warning('required parameters missing for mistral')
            self.stop(data, error=True)
            return
        try:
            client = client.Client()
            execute = executions.ExecutionManager(client)
            output = execute.create(workflow, task, params)
            self.current_action.output = str(output)
        except Exception as e:
            LOG.exception(e)
            self.current_action.output = e.message
            self.stop(data, True)
            return None

        self.stop(data)
        return self.current_action.id

    def stop(self, data, error=False, message=None):
        #this will work if not in thread probably, if we change this
        #add the id to the data and context
        if error:
            self.current_action.error()
        else:
            self.current_action.stop()

        self.current_action.save()
        LOG.debug("Task stopped")
