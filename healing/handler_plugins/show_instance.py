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

    def start(self, ctx, data):
        """ do something...  spawn thread?
            :param data ActionData Object
        """
        if not self.can_execute(data):
            raise exceptions.ActionInProgress()

        self.register_action(data)
        try:
            client = utils.get_nova_client(ctx)
            lista = client.servers.get(data.target_resource)
            self.current_action.output = str(lista)
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


    def can_execute(self, data, ctx=None):
        return super(InstanceShow, self).can_execute(data, ctx=ctx)
