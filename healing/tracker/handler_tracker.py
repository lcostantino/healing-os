# -*- encoding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""
Track if the resource is in the expected state
after an action.

This could be done with notification listener, but if we need
to block or notifications are not active?.
It's very unperformant... but if we decide to switch logic 
will be here. Ex: asking a notification service if XXX.resize.start/end has arrived or not, but again
if there's another system consuming those notifications ?
"""

from stevedore import extension
from healing import exceptions
from healing.handler_plugins import plugin_config
from healing.openstack.common import log
from healing.openstack.common import threadgroup

LOG = log.getLogger(__name__)


CURRENT_TRACKER = None


class ActionTrack(object):
    def __init__(self, action_obj, track_type='instance', track_component='nova',
                 track_columns={'state': [('Active', True), ('Error', False)]}):
            self.track_type = track_type
            self.track_component = track_component
            self.track_columns = track_columns
            self.track_resource = action_obj.target_id
            self.id = action_obj.id
            self.finished = False
            self.status = "OK"
            
            
class HandlerTracker(object):

    def __init__(self):
        self.ACTION_TRACKS = {}
        pass
    
    def track_action(self, action_track):
        LOG.debug('Adding action to track')
        self.ACTION_TRACKS[action_track.id] = action_track
        
    def is_action_ready(self, action_id):
        """ For block calls. Will be the only one supported now. """
        track = self.ACTION_TRACKS.get(action_id, None)
        if not track:
            LOG.warning('Asking for an unexistent tracking action.')
            return True
        if track_finished:
            pass
        # remove?
        return (track.finished, track.status)
        
    def check_actions():
        # should be a periodic stask
        pass
    
    
    
def get_handler_tracker():
    global CURRENT_TRACKER
    if not CURRENT_TRACKER:
        CURRENT_TRACKER = HandlerTracker()
    return CURRENT_TRACKER
