"""
prepare in the future for real object<>rpc/db versioning
"""
from healing.db import api as db_api
from healing.objects import base
from healing.objects import fields


class SLAContract(base.HealingPersistentObject, base.HealingObject):
    VERSION = "1.0"
    fields = {'id': fields.StringField(),
              'project_id': fields.StringField(nullable=True),
              'type': fields.StringField(),
              'value': fields.StringField(nullable=True),
              'action': fields.StringField(),
              'resource_id': fields.StringField(nullable=True)}

    @staticmethod
    def _from_db_object(sla_contract, db_sla_contract):
        for key in sla_contract.fields:
            sla_contract[key] = db_sla_contract[key]
        sla_contract.obj_reset_changes()
        return sla_contract

    def to_dict(self):
        values = dict()
        for key in self.fields:
            values[key] = self[key]
        return values

    @classmethod
    def from_dict(self, values):
        contract = SLAContract()
        for key in values.keys():
            contract[key] = values[key]
        return contract

    @classmethod
    def get_by_project_id(cls, project_id):
        db_sla_contracts = db_api.sla_contract_get_by_project(project_id)

        sla_contracts = []
        for db_sla_contract in db_sla_contracts:
            sla_contracts.append(cls._from_db_object(cls(), db_sla_contract))

        return sla_contracts

    @classmethod
    def get_by_contract_id(cls, contract_id):
        return db_api.sla_contract_get_by_id(contract_id)

    @classmethod
    def get_all(cls):
        db_sla_contracts = db_api.sla_contract_get_all()

        sla_contracts = []
        for db_sla_contract in db_sla_contracts:
            sla_contracts.append(cls._from_db_object(cls(), db_sla_contract))

        return sla_contracts

    def create(self):
        if self.obj_attr_is_set('id'):
            # TODO: add proper exception
            raise Exception('SLA Contract already created')

        updates = self.obj_get_changes()
        updates.pop('id', None)

        db_sla_contract = db_api.sla_contract_create(updates)
        return self._from_db_object(self, db_sla_contract)

    def save(self):
        updates = self.obj_get_changes()
        updates.pop('id', None)
        db_sla_contract = db_api.sla_contract_update(self.id, updates)
        return self._from_db_object(self, db_sla_contract)

    @classmethod
    def delete(cls, id):
        db_api.sla_contract_delete(id)

