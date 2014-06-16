"""
prepare in the future for real object<>rpc/db versioning
"""
#TODO: create base class- add mixin persisten for updated_at & created_at to update on each save
#TODO: check if we need to add context with session to avoid creating new ones
#TODO: Add action state
import six
import datetime

from healing.objects import base
from healing.objects import fields
from healing.db import api as db_api
from healing.openstack.common import jsonutils

from healing.openstack.common import timeutils

ACTION_STARTED = 'started'
ACTION_FINISHED = 'finished' #mean sucess..
ACTION_ERROR = 'error'
ACTION_PENDING = 'pending'
ACTION_DISCARDED = 'discarded'

class Action(base.HealingPersistentObject, base.HealingObject):
    VERSION = "1.0"
    # no coercion rigth now, in place if we move to objects
    fields = {'id': fields.StringField(),
              'name': fields.StringField(),
              'status': fields.StringField(),
              'action_meta': fields.StringField(nullable=True),
              'target_id': fields.StringField(),
              'request_id': fields.StringField(nullable=True),
              'project_id': fields.StringField(nullable=True),
              'internal_data': fields.StringField(nullable=True),
              'output': fields.StringField(nullable=True)}


    @staticmethod
    def from_data(name=None, target_resource=None,
                 data=None, headers=None, internal_data=None,
                 request_id=None, project_id=None,
                 status=ACTION_PENDING):
        action = Action()
        action.name = name
        action.target_id = target_resource
        
        if data and isinstance(data, six.string_types):
            try:
                data = jsonutils.loads(data)
            except:
                raise
                LOG.error("Invalid data for action. must be dict"
                          "for json string")
                data = None
        action.action_meta_obj = {'headers': headers, 'data': data}
        action.internal_data_obj = internal_data
        action.request_id = request_id
        action.output = None
        action.project_id = project_id
        action.status = status
        return action
    
    @staticmethod
    def _from_db_object(action, db_action):
        for key in action.fields:
            action[key] = db_action[key]
        action.obj_reset_changes()
        return action

    @classmethod
    def get_by_id(cls, action_id):
        db_action = db_api.action_get(action_id)
        return cls._from_db_object(cls(), db_action)

    @classmethod
    def get_by_name_and_target(cls, name, target, updated_time_after=None,
                               status=None, ignore_status=None):
        """ return the last one base on created_at."""
        db_action = db_api.action_get_by_name_and_target(name, target,
                                            updated_time_gt=updated_time_after,
                                            status=status,
                                            ignore_status=ignore_status)
        return cls._from_db_object(cls(), db_action)

    @classmethod
    def get_all_by_name(cls, name):
        filters = {'name': name}
        db_action = db_api.actions_get_all(filters=filters)
        return [cls._from_db_object(cls(), x) for x in db_action]

    @classmethod
    def get_all_by_request_id(cls, req_id):
        filters = {'request_id': req_id}
        db_action = db_api.actions_get_all(filters=filters)
        return [cls._from_db_object(cls(), x) for x in db_action]

    @classmethod
    def get_all(cls, limit=0):
        db_action = db_api.actions_get_all()
        return [cls._from_db_object(cls(), x) for x in db_action]

    def _convert_json(self, data, to_object=True):
        if not data:
            return None #should be '' also.. if to_object==false
        try:
            if to_object:
                return jsonutils.loads(data)
            else:
                return jsonutils.dumps(data)
        except Exception:
            return None

    # it will be removed if we get fields in object in the future
    @property
    def internal_data_obj(self):
        return self._convert_json(self.internal_data)

    @internal_data_obj.setter
    def internal_data_obj(self, data_obj):
        self.internal_data = self._convert_json(data_obj, to_object=False)

    @property
    def action_meta_obj(self):
        return self._convert_json(self.action_meta)

    @action_meta_obj.setter
    def action_meta_obj(self, data_obj):
        self.action_meta = self._convert_json(data_obj, to_object=False)

    def stop(self):
        self.status = ACTION_FINISHED

    def error(self):
        self.status = ACTION_ERROR

    def create(self):
        if self.obj_attr_is_set('id'):
            # TODO: add proper exception
            raise Exception('alredy created')
        updates = self.obj_get_changes()
        updates.pop('id', None)
        db_action = db_api.action_create(updates)
        return self._from_db_object(self, db_action)

    def save(self):
        # this is done by base class in the future... check nova objects
        # ideally, we should track what actually changed
        updates = self.obj_get_changes()
        updates.pop('id', None)
        # we won't get updated_at updated here, but...
        db_action = db_api.action_update(self.id, updates)
        return self._from_db_object(self, db_action)





