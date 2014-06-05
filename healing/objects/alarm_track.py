"""
prepare in the future for real object<>rpc/db versioning

WARNING: Operate AlarmActions tru AlarmEngine!!! never directly
"""
from healing.db import api as db_api
from healing.objects import base
from healing.objects import fields


class AlarmTrack(base.HealingPersistentObject, base.HealingObject):
    VERSION = "1.0"
    fields = {'id': fields.StringField(),
              'alarm_id': fields.StringField(nullable=True),
              'contract_id': fields.StringField(nullable=False),
              'type': fields.StringField(),
              'meter': fields.StringField(),
              # It's a string, because we may support other monitoring tools
              # that report status value
              'threshold': fields.StringField(),
              'operator': fields.StringField(nullable=True),
              'period': fields.IntegerField(),
              'evaluation_period': fields.IntegerField(default=1),
              'query': fields.StringField(nullable=True),
              'statistic': fields.StringField(nullable=True),
              'action': fields.StringField(nullable=True)}

    def same_values(self, obj1):
        """
        We don't use == operator, since we don't check
        id neither contract_id."""
        keys = set(self.fields.keys())
        keys -= set(('id', 'contract_id', 'created_at', 'updated_at'))
        for key in keys:
            if obj1[key] != self[key]:
                return False
        return True

    @staticmethod
    def _from_db_object(alarm_track, db_alarm_track):
        for key in alarm_track.fields:
            alarm_track[key] = db_alarm_track[key]
        alarm_track.obj_reset_changes()
        return alarm_track

    def to_dict(self):
        values = dict()
        for key in self.fields:
            values[key] = self[key]
        return values

    @classmethod
    def get_by_id(cls, alarm_track_id):
        db_alarm_track = db_api.alarm_track_get(alarm_track_id)
        return cls._from_db_object(cls(), db_alarm_track)

    @classmethod
    def get_by_alarm_id(cls, alarm_id):
        """ If single alarm, can contains multiples records."""
        filters = {'alarm_id': alarm_id}
        objs = db_api.alarm_tracks_get_all(filters) or []
        return [cls._from_db_object(cls(), x) for x in objs]

    @classmethod
    def get_by_contract_id(cls, contract_id):
        filters = {'contract_id': contract_id}
        db_alarm_track = db_api.alarm_track_get_by_filters(filters)
        return cls._from_db_object(cls(), db_alarm_track)

    @classmethod
    def get_by_type(cls, alarm_type):
        """ the first one."""
        filters = {'type': alarm_type}
        db_alarm_track = db_api.alarm_track_get_by_filter(filters)
        return cls._from_db_object(cls(), db_alarm_track)

    def delete(self):
        if self.obj_attr_is_set('id'):
            db_api.alarm_track_delete(self.id)
        return

    def create(self):
        if self.obj_attr_is_set('id'):
            # TODO: add proper exception
            raise Exception('Alarm Track already created')

        updates = self.obj_get_changes()
        updates.pop('id', None)

        db_alarm_track = db_api.alarm_track_create(updates)
        return self._from_db_object(self, db_alarm_track)

    def save(self):
        updates = self.obj_get_changes()
        updates.pop('id', None)
        db_alarm_track = db_api.alarm_track_update(self.id, updates)
        return self._from_db_object(self, db_alarm_track)

    # TODO: ADD OBJECT LIST FROM NOVA FOR THIS
    @classmethod
    def get_all_by_type(cls, alarm_type):
        filters = {'type': alarm_type}
        objs = db_api.alarm_tracks_get_all(filters) or []
        return [cls._from_db_object(cls(), x) for x in objs]
