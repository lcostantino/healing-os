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
Action manager service
"""
from oslo.config import cfg
from healing import config
from oslo import messaging


from healing import exceptions
from healing.tracker.handler_tracker import get_handler_tracker as tracker
from healing import manager
from healing.objects import tracker
from healing.openstack.common import excutils
from healing.openstack.common import importutils
from healing.openstack.common import jsonutils
from healing.openstack.common import log as logging
from healing.openstack.common import periodic_task



LOG = logging.getLogger(__name__)

class TrackerManager(manager.Manager):
    target = messaging.Target(version='1.0')

    def __init__(self, scheduler_driver=None, *args, **kwargs):
        super(TrackerManager, self).__init__(service_name='actiontracker',
                                               *args, **kwargs)
        
        
    def track_action(self, context, track_action):
        print "TRCK ction"
        handler_tracker().add_track(track_action)
        
        
