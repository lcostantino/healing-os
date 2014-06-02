"""
prepare in the future for real object<>rpc/db versioning
"""
from healing.db import api as db_api
from healing.openstack.common import jsonutils

class SLAContract(object):
    fields = {'id': None,
              'project_id': None,
              'type': None,
              'value': None,
              'updated_at': None, #datetime.datetime.utcnow(),
              'created_at': None, #datetime.datetime.utcnow(),
              'deleted_at': None} #datetime.datetime.utcnow(),

    def __init__(self):
        self.__dict__.update(self.fields)

    @staticmethod
    def _from_db_object(sla_contract, db_sla_contract):
        fields = set(sla_contract.fields)
        for key in fields:
            setattr(sla_contract, key, db_sla_contract[key])
        return sla_contract

    @classmethod
    def get_by_project_id(cls, project_id):
        db_sla_contracts = db_api.sla_contract_get_by_project(project_id)

        sla_contracts = []
        for db_sla_contract in db_sla_contracts:
            sla_contracts.append(cls._from_db_object(cls(), db_sla_contract))

        return sla_contracts

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

    def create(self):
        if getattr(self, 'id'):
            # TODO: add proper exception
            raise Exception('SLA Contract already created')
        #this is done by base class in the future... check nova objects
        updates = {}
        for i in self.fields:
            updates[i] = getattr(self, i)
        updates.pop('id', None)
        db_sla_contract = db_api.sla_contract_create(updates)
        return self._from_db_object( self, db_sla_contract)

    def save(self):
        # this is done by base class in the future... check nova objects
        # ideally, we should track what actually changed
        updates = {}
        for i in self.fields:
            updates[i] = getattr(self, i, None)
        updates.pop('id', None)
        # we won't get updated_at updated here, but...
        db_sla_contract = db_api.sla_contract_update(self.id, updates)
        return self._from_db_object( self, db_sla_contract)
