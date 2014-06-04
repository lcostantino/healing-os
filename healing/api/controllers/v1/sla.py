# -*- coding: utf-8 -*-
#
# Copyright 2014 - Intel
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import pecan
from pecan import rest
from pecan import abort
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from healing.openstack.common import log as logging
from healing.api.controllers import resource
from healing.objects import sla_contract as objects

LOG = logging.getLogger(__name__)


class SLAContract(resource.Resource):
    """SLA contract resource."""

    id = wtypes.text
    project_id = wtypes.text
    type = wtypes.text
    value = wtypes.text
    action = wtypes.text

    @classmethod
    def from_object(cls, obj_sla_contract):
        return cls().from_dict(obj_sla_contract.to_dict())

    def to_object(self):
        obj = objects.SLAContract()
        if self.id:
            obj.id = self.id
        obj.project_id = self.project_id or None
        obj.type = self.type
        obj.value = self.value or None
        obj.action = self.action

        return obj


class SLAContracts(resource.Resource):
    """SLA contract resource list."""

    contracts = [SLAContract]


class SLAContractController(rest.RestController):

    @wsme_pecan.wsexpose(SLAContracts, wtypes.text)
    def get(self, project_id):
        LOG.debug("Fetch SLAContract controller - get")
        values = objects.SLAContract.get_by_project_id(project_id)

        contracts = [SLAContract.from_object(val) for val in values]
        return SLAContracts(contracts=contracts)

    @wsme_pecan.wsexpose(SLAContract, body=SLAContract)
    def post(self, sla_contract):
        return SLAContract.from_object(sla_contract.to_object().create())

    @wsme_pecan.wsexpose(SLAContract, wtypes.text, body=SLAContract)
    def put(self, id, sla_contract):
        sla_contract.id = id
        return SLAContract.from_object(sla_contract.to_object().save())

    @wsme_pecan.wsexpose(SLAContracts)
    def get(self):
        return SLAContracts(objects.SLAContract.get_all())

    @wsme_pecan.wsexpose(wtypes.text)
    def delete(id):
        objects.SLAContract.delete(id)

class SLAAlarmingController(rest.RestController):

    @wsme_pecan.wsexpose()
    def get_all(self):
        LOG.debug("Fetch SLAAlarming controller - get_all")

    @wsme_pecan.wsexpose()
    def get(self):
        LOG.debug("Fetch SLAAlarming controller - get")

    @wsme_pecan.wsexpose()
    def post(self):
        LOG.debug("Fetch SLAAlarming controller - post")


class SLAController(rest.RestController):
    @wsme_pecan.wsexpose()
    def get_all(self):
        LOG.debug("Fetch SLA controller - get_all")

    @wsme_pecan.wsexpose()
    def get(self):
        LOG.debug("Fetch SLA controller - get")

    @wsme_pecan.wsexpose()
    def post(self):
        LOG.debug("Fetch SLA controller - post")

    contract = SLAContractController()
    alarming = SLAAlarmingController()


