from healing import config
from healing import utils
from healing import handler_manager
from healing.handler_plugins import action_data
from healing.engine.alarms import manager
from healing.engine.alarms import filters

from healing.openstack.common import log as logging

logging.setup('heal')

config.parse_args()
ctx = utils.build_context()

mg = handler_manager.get_plugin_handler()

to_run = []
for x in range(1,20):
    to_run.append(action_data.ActionData(name='evacuate', target_resource='s', data={}))
    

           
print mg.start_plugins_group(ctx, to_run)
"""
#nv = utils.get_nova_client(ctx)

#print utils.get_nova_vms(nv)
#print utils.get_nova_vms(nv, tenant_id=22222)
#print utils.get_nova_vms(nv, host='ubuntu-SVT13125CLS')




"""
ss = manager.alarm_build_by_type(ctx, 'host_down_unique', contract_id='222', meter='services.compute_host.down',
                                  threshold=1, operator='eq', period=10)
ss.create()



ss = manager.alarm_build_by_type(ctx, 'host_down_unique', meter='sss', contract_id=2)
print ss.contract_id
print manager.get_all_by_type(ctx, 'host_down_unique')


cm = alarm.HostDownUniqueAlarm(ctx=ctx, contract_id='111', 
                           meter='cpu_util', threshold=1,
                           operator='eq',  period=10)


cm.create()


cm = alarm.HostDownUniqueAlarm.get_by_id(ctx=ctx, 
                                         alarm_track_id='7119beb4-b397-4514-8e22-dc0daf9cb8e9')
cm.meter = 'caca'
cm.options = {'repeat': False}
cm.update()
#cm.update()
#cm.delete()
"""



alarmas = alarm.HostDownUniqueAlarm.get_all_by_type(ctx=ctx)
alarmas[0].delete()

for x in range(0,5):
    cm = alarm.HostDownUniqueAlarm(ctx=ctx, contract_id='111', 
           meter='cpu_util', threshold=1,
           operator='eq',  period=10)
    cm.create()
"""
"""
alarmas = alarm.HostDownUniqueAlarm.get_all_by_type(ctx=ctx)
for x in alarmas:
    x.meter = 'FirstChangeShuldUpdate'

import time
alarmas = alarm.HostDownUniqueAlarm.get_all_by_type(ctx=ctx)
for x in alarmas[:-1]:
    x.delete()
    
print 'ging to elete last one'
time.sleep(5)
alarmas[-1].delete()



####################33 resource alarm

cm = alarm.ResourceAlarm(ctx=ctx, contract_id='111', 
                         meter='cpu_util', threshold=1,
                         operator='eq',  period=10,
                        resource_id='b7a507b8-96cf-4433-b862-8c19462601a2')


cm.create()


alarmas = alarm.ResourceAlarm.get_all_by_type(ctx=ctx)
for x in alarmas:
    x.delete()


alarmas = manager.get_all_by_type(ctx, 'host_down_unique')
print alarmas[0].affected_resources(meter='services.compute_host.down', result_process=filters.RemoveIfSeenInTwoPeriods,
                                    period=alarmas[0].period, delta_seconds=3600*48)

"""