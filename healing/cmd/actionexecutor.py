from healing import service
from healing import objects
from healing import config
from healing.rpc import rpc
from healing.openstack.common import service as os_service
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
objects.register_all()
server = service.Service.create(binary='healing-action_executor', topic=config.CONF.action_executor.topic,
                                manager=config.CONF.action_executor.manager)

#server.start()
#server.wait()
service.serve(server, workers=config.CONF.action_executor.workers)
service.wait()
print "SERVED"
