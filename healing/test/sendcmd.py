from healing import service
from healing import config
from healing.rpc import rpc

from healing.openstack.common import log as logging


from healing import service
from healing import context
from healing import config
from healing.rpc import rpc
from healing.actionexecutor import rpcapi
from healing.openstack.common import log as logging
from healing.objects import action
import sys
from healing.openstack.common import log as logging

import eventlet

eventlet.monkey_patch(
    os=True,
    select=True,
    socket=True, # esto hace falta para cambiar el transport...
    thread=False if '--use-debugger' in sys.argv else True,
    time=True)
                    

config.parse_args()
logging.setup('Healing')
rpc.init(config.CONF)

ctx = context.Context('pepe')
act = action.Action({'id': '22', 'name': 33, 'status' : 44, 'target_id': 222})
print act
print "OUTPUT:" , rpcapi.ActionAPI().test(ctx, {'s':'2'})
