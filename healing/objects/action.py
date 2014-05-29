"""
prepare in the future for real object<>rpc/db versioning
"""
#TODO: create base class- add mixin persisten for updated_at & created_at to update on each save
#TODO: check if we need to add context with session to avoid creating new ones
#TODO: Add action state
import datetime

from healing.db import api as db_api
from healing.openstack.common import jsonutils

from healing.openstack.common import timeutils

ACTION_STARTED = 'started'
ACTION_FINISHED = 'finished' #mean sucess..
ACTION_ERROR = 'error'


class Action(object):
    # no coercion rigth now, in place if we move to objects
    fields = {'id': None,
              'name': None,
              'source': None,
              'status': None,
              'action_meta': None,
              'target_id': None,
              'project_id': None,
              'updated_at': None, #datetime.datetime.utcnow(),
              'created_at': None, #datetime.datetime.utcnow(),
              'internal_data': None}

    def __init__(self):
        # The metaclass should add the fiels to the object dict , since its
        # not ready, hack it.
        self.__dict__.update(self.fields)

    @staticmethod
    def _from_db_object(action, db_action):
        fields = set(action.fields)
        for key in fields:
            # TODO: add object assign
            #action[key] = db_action[key]
            setattr(action, key, db_action[key])
        return action

    @classmethod
    def get_by_id(cls, action_id):
        db_action = db_api.action_get(action_id)
        return cls._from_db_object(cls(), db_action)

    @classmethod
    def get_by_name_and_target(cls, name, target, updated_time_after=None,
                               status=None):
        """ return the last one base on created_at."""
        db_action = db_api.action_get_by_name_and_target(name, target,
                                            updated_time_gt=updated_time_after,
                                            status=status)
        return cls._from_db_object(cls(), db_action)


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
        if getattr(self, 'id'):
            # TODO: add proper exception
            raise Exception('alredy created')
        #this is done by base class in the future... check nova objects
        updates = {}
        for i in self.fields:
            updates[i] = getattr(self, i)
        updates.pop('id', None)
        db_action = db_api.action_create(updates)
        return self._from_db_object( self, db_action)

    def save(self):
        # this is done by base class in the future... check nova objects
        # ideally, we should track what actually changed
        updates = {}
        for i in self.fields:
            updates[i] = getattr(self, i, None)
        updates.pop('id', None)
        # we won't get updated_at updated here, but...
        db_action = db_api.action_update(self.id, updates)
        return self._from_db_object( self, db_action)





