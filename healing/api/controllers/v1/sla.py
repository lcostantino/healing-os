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
from pecan import abort
from pecan import rest
import six
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan


from healing import utils
from healing.actionexecutor import rpcapi as action_api
from healing.api.controllers import resource
from healing.api.controllers.v1 import action
from healing.engine.sla.manager import SLAContractEngine
from healing.engine.sla.manager import SLAAlarmingEngine
from healing.openstack.common import jsonutils
from healing.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class SLAContract(resource.Resource):
    """SLA contract resource."""

    id = wtypes.text
    project_id = wtypes.text
    type = wtypes.text
    value = wtypes.text
    action = wtypes.text
    resource_id = wtypes.text
    alarm_data = wtypes.text
    action_options = wtypes.text
    name = wtypes.text


class SLAAlarm(resource.Resource):
    """SLA alarm resource."""

    current = wtypes.text
    alarm_id = wtypes.text
    reason = wtypes.text
    previous = wtypes.text


class FailureTrack(resource.Resource):
    """Failure Track resource."""

    id = wtypes.text
    created_at = wtypes.datetime.datetime
    alarm_id = wtypes.text
    data = wtypes.text
    contract_names = wtypes.text

class SLAContracts(resource.Resource):
    """SLA contract resource list."""

    contracts = [SLAContract]


class FailureTracks(resource.Resource):
    """Failure Track resource list."""

    failures = [FailureTrack]


class SLAContractController(rest.RestController):

    def __init__(self):
        self.engine = SLAContractEngine()

    @wsme_pecan.wsexpose(SLAContract, body=SLAContract, status_code=201)
    def post(self, contract):
        ctx = utils.build_context(None, True)
        contract_dict = self.engine.create(ctx, contract.to_dict())
        return SLAContract.from_dict(contract_dict)

    @wsme_pecan.wsexpose(SLAContract, wtypes.text)
    def get(self, contract_id):
        contract_dict = self.engine.get(contract_id)
        return SLAContract.from_dict(contract_dict)

    @wsme_pecan.wsexpose(SLAContract, wtypes.text, body=SLAContract)
    def put(self, contract_id, contract):
        ctx = utils.build_context(None, True)
        contract.id = contract_id
        contract_dict = self.engine.update(ctx, contract.to_dict())
        return SLAContract.from_dict(contract_dict)

    @wsme_pecan.wsexpose(SLAContracts)
    def get_all(self):
        contract_dicts = self.engine.get_all()
        contracts = [SLAContract.from_dict(obj) for obj in contract_dicts]

        return SLAContracts(contracts=contracts)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, id):
        ctx = utils.build_context(None, True)
        self.engine.delete(ctx, id)


class SLAAlarmingController(rest.RestController):

    def __init__(self):
        self.engine = SLAAlarmingEngine()
        self.action_api = action_api.ActionAPI()

    @pecan.expose()
    def post(self):
        """
        ceilometer don't send content-type, so need to parse it manually
        just in case.
        There should be a way for this, but it can be dynamic based
        on source. Still need to look for, since we miss the mime type
        handled by wsme
        """
        source = pecan.request.GET.get('source')
        status = pecan.request.GET.get('status')
        contract_id = pecan.request.GET.get('contract_id')
        resource_id = pecan.request.GET.get('resource_id')
        body = six.moves.urllib_parse.unquote_plus(pecan.request.body)
        if body and body[-1] == '=':
            body = body[:-1]

        #validate body
        ctx = utils.get_context_req(pecan.request)
        if not status or not source:
            abort(400, 'Status and Source are required')
        alarm = jsonutils.loads(body)
        if status == 'alarm':
            self.action_api.alarm(ctx, alarm.get('alarm_id'), source=source,
                              contract_id=contract_id,
                              resource_id=resource_id)
        return ""


class SLATrackingController(rest.RestController):

    def __init__(self):
        self.engine = SLAAlarmingEngine()

    @wsme_pecan.wsexpose(FailureTracks)
    def get_all(self):
        failure_dicts = self.engine.track_failure_get_all()
        failures = [FailureTrack.from_dict(obj) for obj in failure_dicts]
        return FailureTracks(failures=failures)


class SLAController(rest.RestController):

    contract = SLAContractController()
    alarming = SLAAlarmingController()
    tracking = SLATrackingController()
    actions = action.ActionsController()
