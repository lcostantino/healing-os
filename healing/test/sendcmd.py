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
ACT_OPT = {"workflow":"SendMail", "task":"sendResultEmail", "params": {"admin_email": "root@localhost", "smtp_server": "localhost", "output": "salida"}}

act = action.Action.from_data(name='mistral',
                             status= 'pending', 
                             target_resource='222', 
                             request_id='2222-3333',
                             data=ACT_OPT)
act.create()
            
print "OUTPUT:" , rpcapi.ActionAPI().run_action(ctx, act)
