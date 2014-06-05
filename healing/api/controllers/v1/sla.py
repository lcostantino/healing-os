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

from pecan import rest
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from healing import utils
from healing.api.controllers import resource
from healing.engine.sla.manager import SLAEngine
from healing.openstack.common import log as logging
from healing.objects import sla_contract as objects


LOG = logging.getLogger(__name__)


class SLAContract(resource.Resource):
    """SLA contract resource."""

    id = wtypes.text
    project_id = wtypes.text
    type = wtypes.text
    value = wtypes.text
    action = wtypes.text


class SLAContracts(resource.Resource):
    """SLA contract resource list."""

    contracts = [SLAContract]


class SLAContractController(rest.RestController):

    def __init__(self):
        self.engine = SLAEngine()

    @wsme_pecan.wsexpose(SLAContract, wtypes.text)
    def get(self, contract_id):
        contract_dict = self.engine.get(contract_id)
        return SLAContract.from_dict(contract_dict)

    @wsme_pecan.wsexpose(SLAContract, body=SLAContract, status_code=201)
    def post(self, sla_contract):
        ctx = utils.build_context(None, True)
        contract_dict = self.engine.create(ctx, sla_contract.to_dict(), 120)
        return SLAContract.from_dict(contract_dict)

    @wsme_pecan.wsexpose(SLAContract, wtypes.text, body=SLAContract)
    def put(self, id, sla_contract):
        ctx = utils.build_context(None, True)
        sla_contract.id = id
        contract_dict = self.engine.update(ctx, sla_contract.to_dict(), 120)
        return SLAContract.from_dict(contract_dict)

    @wsme_pecan.wsexpose(SLAContracts)
    def get(self):
        contract_dicts = self.engine.get_all()
        contracts = [SLAContract.from_dict(obj) for obj in contract_dicts]

        return SLAContracts(contracts=contracts)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, id):
        ctx = utils.build_context(None, True)
        self.engine.delete(id)


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

