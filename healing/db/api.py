# -*- coding: utf-8 -*-
#
# Copyright 2014 - Intel.
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

from oslo.config import cfg
from healing.openstack.common.db import api as db_api
from healing.openstack.common import log as logging

CONF = cfg.CONF
# actions
#based on mistral
CONF.import_opt('backend', 'healing.openstack.common.db.options',
                group='database')


_BACKEND_MAPPING = {
    'sqlalchemy': 'healing.db.sqlalchemy.api',
}

IMPL = db_api.DBAPI(CONF.database.backend, backend_mapping=_BACKEND_MAPPING)
LOG = logging.getLogger(__name__)


def setup_db():
    IMPL.setup_db()


def drop_db():
    IMPL.drop_db()


# TODO: check if we want to pss context with the current session
# to avoid creating new ones.

def action_get(action_id):
    return IMPL.action_get(action_id)


def action_get_by_name_and_target(name, target, updated_time_gt=None,
                                  status=None):
    filters = {'name': name,
               'target_id': target}
    if status:
        filters['status'] = status
    return IMPL.action_get_by_filter(filters, updated_time_gt=updated_time_gt)


def action_get_by_filter(filters):
    return IMPL.action_get_by_filter(filters)


def action_create(values):
    return IMPL.action_create(values)


def action_update(action_id, values):
    return IMPL.action_update(action_id, values)


def action_delete(action_id):
    IMPL.action_delete(action_id)


def actions_get_all(filters=None, order='-created-at'):
    if not filters:
        filters = {}
    return IMPL.actions_get_all(filters, order_by=order)

###SLA_CONTRACT###


def sla_contract_get_by_project(project):
    return IMPL.sla_contract_get_by_project(project)


def sla_contract_get_by_id(id):
    return IMPL.sla_contract_get_by_id(id)


def sla_contract_update(sla_contract_id, values):
    return IMPL.sla_contract_update(sla_contract_id, values)


def sla_contract_create(values):
    return IMPL.sla_contract_create(values)

    
def sla_contract_delete(sla_contract_id):
    return IMPL.sla_contract_delete(sla_contract_id)


def sla_contract_get_all():
    return IMPL.sla_contract_get_all()
      

#########3 ALARM track 3###############3
def alarm_track_get(alarm_track_id):
    return IMPL.alarm_track_get(alarm_track_id)


def alarm_track_get_by_name_and_target(name, target, updated_time_gt=None,
                                  status=None):
    filters = {'name': name,
               'target_id': target}
    if status:
        filters['status'] = status
    return IMPL.alarm_track_get_by_filter(filters, updated_time_gt=updated_time_gt)


def alarm_track_get_by_filter(filters):
    return IMPL.alarm_track_get_by_filter(filters)


def alarm_track_create(values):
    return IMPL.alarm_track_create(values)


def alarm_track_update(alarm_track_id, values):
    return IMPL.alarm_track_update(alarm_track_id, values)


def alarm_track_delete(alarm_id):
    IMPL.alarm_track_delete(alarm_id)


def alarm_tracks_get_all(filters=None, order='created_at'):
    if not filters:
        filters = {}
    return IMPL.alarm_tracks_get_all(filters, order=order)


###SLA_CONTRACT###

def failure_track_get_all():
    return IMPL.failure_track_get_all()


def failure_track_create(values):
    return IMPL.failure_track_create(values)
