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
from healing.db.sqlalchemy.models import SLAContract

from healing.openstack.common import log as logging
from healing.api.controllers import resource
from healing.objects import sla_contract as objects

LOG = logging.getLogger(__name__)


class SLAContract(resource.Resource):
    """SLA contract resource."""

    project_id = wtypes.text
    type = wtypes.text
    value = wtypes.text


class SLAContracts(resource.Resource):
    """SLA contract resource list."""

    contracts = [SLAContract]


class SLAContractController(rest.RestController):

    @wsme_pecan.wsexpose(None, wtypes.text)
    def get(self, project_id):
        LOG.debug("Fetch SLAContract controller - get")
        contracts = objects.SLAContract.get_by_project_id(project_id)
        return SLAContracts(contracts=contracts)

    @wsme_pecan.wsexpose(None, wtypes.text, wtypes.text, wtypes.text)
    def post(self, project_id, type, value):
        LOG.debug("Fetch SLAContract controller - post")
        objects.SLAContract(project_id, type, value).create()


class SLAMonitoringController(rest.RestController):

    @wsme_pecan.wsexpose()
    def get_all(self):
        LOG.debug("Fetch SLAMonitoring controller - get_all")

    @wsme_pecan.wsexpose()
    def get(self):
        LOG.debug("Fetch SLAMonitoring controller - get")

    @wsme_pecan.wsexpose()
    def post(self):
        LOG.debug("Fetch SLAMonitoring controller - post")


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
    monitoring = SLAMonitoringController()


