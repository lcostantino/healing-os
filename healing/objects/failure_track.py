"""
prepare in the future for real object<>rpc/db versioning
"""
from healing.db import api as db_api
from healing.objects import base
from healing.objects import fields


class FailureTrack(base.HealingPersistentObject, base.HealingObject):
    VERSION = "1.0"
    fields = {'id': fields.StringField(),
              'time': fields.DateTimeField(),
              'alarm_id': fields.StringField(),
              'data': fields.StringField(nullable=True)}

    @staticmethod
    def _from_db_object(failure_track, db_failure_track):
        for key in failure_track.fields:
            failure_track[key] = db_failure_track[key]
        failure_track.obj_reset_changes()
        return failure_track

    def to_dict(self):
        values = dict()
        for key in self.fields:
            values[key] = self[key]
        return values

    def from_dict(self, values):
        for key in values.keys():
            self[key] = values[key]

    @classmethod
    def get_all(cls, start_date=None, end_date=None):

        filters = {}

        db_failure_tracks = db_api.failure_track_get_all(start_date, end_date)

        failure_tracks = []
        for db_failure_track in db_failure_tracks:
            failure_tracks.append(cls._from_db_object(cls(), db_failure_track))

        return failure_tracks

    def create(self):
        if self.obj_attr_is_set('id'):
            # TODO: add proper exception
            raise Exception('Failure Track already created')

        updates = self.obj_get_changes()
        updates.pop('id', None)

        db_failure_track = db_api.failure_track_create(updates)
        return self._from_db_object( self, db_failure_track)

