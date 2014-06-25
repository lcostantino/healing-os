# Copyright (c) 2010 OpenStack Foundation
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Notification listener service
"""
from oslo.config import cfg
from healing import config
from oslo import messaging

from healing import context
from healing import exceptions
from healing.actionexecutor import rpcapi as action_api
from healing.engine.alarms import manager as alarm_manager
from healing.engine.alarms import generic_alarms
from healing import manager
from healing.objects import alarm_track
from healing.openstack.common import excutils
from healing.openstack.common import importutils
from healing.openstack.common import jsonutils
from healing.openstack.common import log as logging
from healing.openstack.common import periodic_task
from healing import utils


LOG = logging.getLogger(__name__)

class TrackerManager(manager.Manager):
    target = messaging.Target(version='1.0')
    event_types_listen = set()

    def __init__(self, scheduler_driver=None, *args, **kwargs):
        super(TrackerManager, self).__init__(service_name='actiontracker',
                                               *args, **kwargs)
        self.action_api = action_api.ActionAPI()

    def warn(self, ctxt, publisher_id, event_type, payload, metadata):
        self._process_notification(ctxt, event_type, payload, metadata)

    def error(self, ctxt, publisher_id, event_type, payload, metadata):
        self._process_notification(ctxt, event_type, payload, metadata)

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        self._process_notification(ctxt, event_type, payload, metadata)

    def debug(self, ctxt, publisher_id, event_type, payload, metadata):
        self._process_notification(ctxt, event_type, payload, metadata)

    def _process_notification(self, ctxt, event_type, payload, metadata):
        ctxt = context.Context.from_dict(ctxt)
        if event_type not in self.event_types_listen:
            return

        # The first one we get, is the only one we trigger since they
        # the are fetch by priority ( resource & prject ), (project), 
        # (generic)

        project_id = payload.get('tenant_id')
        resource_id = payload.get('instance_id')
        # check if there's another id instead of instance_id
        try:
            alarms = alarm_track.AlarmTrack.get_all_by_project_or_resource(
                                                           event_type,
                                                           project=project_id,
                                                           resource=resource_id)
            if alarms:
                best_match = alarms[0]
                # project_id because it can be a non-tenant based alarm
                self.action_api.alarm(ctxt, alarm_id=best_match.id, source='notifier',
                                      resource_id=resource_id, 
                                      project_id=project_id)
        except Exception as exc:
            LOG.exception(exc)
            
    @periodic_task.periodic_task(run_immediately=True)
    def update_notification_alarms(self, ctx):
        # Update the list of event_types we are interesed in
        # from the db
        try:
            alarms = alarm_manager.get_all_by_type(ctx,
                                    generic_alarms.NotificationAlarm.ALARM_TYPE)
        except Exception as e:
            LOG.exception(e)
            return
        listen_types = [x.meter for x in alarms]
        self.event_types_listen = set(listen_types)
        LOG.debug(self.event_types_listen)

