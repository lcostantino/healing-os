from healing.handler_plugins import base

from healing import exceptions
from healing.openstack.common import log as logging
from healing import utils


LOG = logging.getLogger(__name__)

class Mistral(base.HandlerPluginBase):
    """evacuate VM plugin.

    Data format in action_meta is:
        'evacuate_host': True  if evacuating the entire host
    """
    DESCRIPTION = "Run mistral workflow"
    NAME = "mistral"

    def start(self, ctx, data):
        pass


    def stop(self, data, error=False, message=None):
        pass


    def can_execute(self, data, ctx=None):
        """
        :param data ActionData Obj
        move to parent?
        """
        return super(Mistral, self).can_execute(data, ctx=ctx)
