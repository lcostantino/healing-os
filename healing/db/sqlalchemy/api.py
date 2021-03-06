# -*- coding: utf-8 -*-
#
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

import sys
import sqlalchemy as sa
from sqlalchemy.sql import or_
from sqlalchemy.sql.expression import desc, asc

from healing import config
from healing import exceptions as exc
from healing.db.sqlalchemy import model_base as base
from healing.db.sqlalchemy import models as m
from healing.openstack.common.db.sqlalchemy import session as db_session
from healing.openstack.common import log as logging
from healing.openstack.common.db import exception as db_exc


LOG = logging.getLogger(__name__)


_DB_SESSION_THREAD_LOCAL_NAME = "db_sql_alchemy_session"

_MASTER_FACADE = None
def _create_facade_lazily(use_slave=False):
    global _MASTER_FACADE
    if _MASTER_FACADE is None:
        _MASTER_FACADE = db_session.EngineFacade(
                                   config.CONF.database.connection,
                                   **dict(config.CONF.database.iteritems())
                        )
    return _MASTER_FACADE


def get_engine(use_slave=False):
    facade = _create_facade_lazily(use_slave)
    return facade.get_engine()


def get_session(use_slave=False, **kwargs):
    facade = _create_facade_lazily(use_slave)
    return facade.get_session(**kwargs)


def get_backend():
    """The backend is this module itself."""
    return sys.modules[__name__]


def setup_db():
    try:
        engine = get_engine()
        base.HealingBase.metadata.create_all(engine)
    except sa.exc.OperationalError as e:
        LOG.exception("Database registration exception: %s", e)
        return False
    return True


def get_order(order):
    """Get desc/asc based on -name/name."""
    if not order:
        return order

    if order[0] == '-':
        return order[1:] + ' DESC'
    return order

def model_query(model, session=None):
    """Query helper.

    :param model: base model to query
    :param context: context to query under
    :param project_only: if present and context is user-type, then restrict
            query to match the context's tenant_id.
    """
    if not session:
        session = get_session()
    return session.query(model)


def action_create(values):
    #TODO: move to @session_aware
    session = get_session()
    with session.begin():
        action = m.Action()
        action.update(values.copy())

        try:
            action.save(session)
        except db_exc.DBDuplicateEntry as e:
            raise exc.DBDuplicateEntry("Duplicate entry for Action: %s"
                                       % e.columns)

        return action

def action_update(action_id, values):
    session = get_session()
    with session.begin():
        action = _action_get(action_id)
        if not action:
            raise exc.NotFoundException("action not found [action_id=%s]" %
                                        action_id)

        action.update(values.copy())
        action.save(session)
        return action


def action_delete(action_id):
    session = get_session()
    with session.begin():
        res = model_query(m.Action, session=session).filter_by(id=action_id)\
                                                    .delete()
        if not res:
            raise exc.NotFoundException("Action not found [action_id=%s]" %
                                        action_id)


def action_get(action_id):
    return _action_get(action_id)


def actions_get_all(filters=None, order='-created_at'):
    if not filters:
        filters = {}
    return _actions_get_all(filters)


def _actions_get_all(filters, order='-created_at'):
    query = model_query(m.Action)
    return query.filter_by(**filters).order_by(get_order(order)).all()


def action_get_by_filter(filters, updated_time_gt=None, order='-created_at'):
    """
    :param updated_time_gt: if set, will do updated_at > updated_time_gt
    """
    query = model_query(m.Action)
    ignore_status = filters.pop('ignore_status', None)
    query = query.filter_by(**filters)
    if updated_time_gt:
        query = query.filter((m.Action.updated_at >= updated_time_gt) |
                             (m.Action.create_at >= updated_time_gt))
    if ignore_status:
        query = query.filter(m.Action.status != ignore_status)
    result = query.order_by(get_order(order)).first()
    if not result:
        raise exc.NotFoundException("action not found [filters=%s]" %
                                     filters)

    return result

#TODO: move exception to db/api.py? may be much better to abstract
def _action_get(action_id):
    query = model_query(m.Action)
    obj = query.filter(m.Action.id==action_id).first()
    if not obj:
        raise exc.NotFoundException()
    return obj

#setup_db()

###SLA_CONTRACT###

def sla_contract_get_by_project(project):
    query = model_query(m.SLAContract)
    return query.filter_by(project_id=project).all()


def sla_contract_get_by_id(sla_contract_id):
    query = model_query(m.SLAContract)
    obj = query.filter_by(id=sla_contract_id).first()
    if not obj:
        raise exc.NotFoundException('SLA Contract not found')
    return obj


def sla_contract_update(sla_contract_id, values):
    session = get_session()
    with session.begin():
        sla_contract = sla_contract_get_by_id(sla_contract_id)
        if not sla_contract:
            raise exc.NotFoundException('SLA contract not found')

        sla_contract.update(values.copy())
        sla_contract.save(session=session)
        return sla_contract


def sla_contract_create(values):
    #TODO: move to @session_aware
    session = get_session()
    with session.begin():
        contract = m.SLAContract()
        contract.update(values.copy())

        try:
            contract.save(session)
        except db_exc.DBDuplicateEntry as e:
            raise exc.DBDuplicateEntry("Duplicate entry for contract: %s"
                                       % e.columns)

        return contract

def sla_contract_delete(sla_contract_id):
    session = get_session()
    with session.begin():
        res = model_query(m.SLAContract, session=session).\
            filter_by(id=sla_contract_id).delete()
        if not res:
            raise exc.NotFoundException("SLA Contract not found "
                                        "[contract_id=%s]" % sla_contract_id)


def sla_contract_get_all():
    query = model_query(m.SLAContract)
    return query.all()

########################

def alarm_track_create(values):
    #TODO: move to @session_aware
    session = get_session()
    with session.begin():
        alarm_track = m.AlarmTrack()
        alarm_track.update(values.copy())

        try:
            alarm_track.save(session)
        except db_exc.DBDuplicateEntry as e:
            raise exc.DBDuplicateEntry("Duplicate entry for alarm_track: %s"
                                       % e.columns)

        return alarm_track

def alarm_track_update(alarm_track_id, values):
    session = get_session()
    with session.begin():
        alarm_track = _alarm_track_get(alarm_track_id)
        if not alarm_track:
            raise exc.NotFoundException("alarm_track not found [alarm_track_id=%s]" %
                                        alarm_track_id)

        alarm_track.update(values.copy())
        alarm_track.save(session)
        return alarm_track


def alarm_track_delete(alarm_track_id):
    session = get_session()
    with session.begin():
        res = model_query(m.AlarmTrack, session=session).filter_by(id=alarm_track_id)\
                                                    .delete()
        if not res:
            raise exc.NotFoundException("alarm_track not found [alarm_track_id=%s]" %
                                        alarm_track_id)


def alarm_track_get(alarm_track_id, multiple_records=False):
    return _alarm_track_get(alarm_track_id, multiple_records)


def alarm_tracks_get_all(filters=None, order='created_at'):
    if not filters:
        filters = {}
    return _alarm_tracks_get_all(filters, order)


def _alarm_tracks_get_all(filters, order='-created_at'):
    query = model_query(m.AlarmTrack)
    res = query.filter_by(**filters).order_by(get_order(order)).all()
    if not res:
        raise exc.NotFoundException('alarms not found for filters')
    return res

def alarm_track_get_by_filter(filters):
    """
    :param updated_time_gt: if set, will do updated_at > updated_time_gt
    """
    query = model_query(m.AlarmTrack)
    query = query.filter_by(**filters)
    result = query.first()
    if not result:
        raise exc.NotFoundException("alarm_track not found [filters=%s]" %
                                     filters)

    return result


#TODO: move exception to db/api.py? may be much better to abstract
def _alarm_track_get(alarm_track_id, multiple_records=False):
    query = model_query(m.AlarmTrack)
    obj = query.filter((m.AlarmTrack.id==alarm_track_id)|
                       (m.AlarmTrack.alarm_id==alarm_track_id))
    if multiple_records:
        obj = obj.all()
    else:
        obj = obj.first()

    if not obj:
        raise exc.NotFoundException()
    return obj

def alarms_by_contract_resource_project(meter, project=None, resource=None):
    """ Retrieve ordered by priority.
        The first one should be triggered. because is the best match.
    """
    contract_q = model_query(m.SLAContract).\
                            filter( or_((m.SLAContract.project_id == project) &
                                    (m.SLAContract.resource_id == resource)) |
                                    or_((m.SLAContract.resource_id == None) &
                                    (m.SLAContract.project_id == project)) |
                                    or_((m.SLAContract.project_id == None) &
                                        (m.SLAContract.resource_id == None))). \
                            subquery()

    query = model_query(m.AlarmTrack)
    query = query.filter(m.AlarmTrack.meter==meter)

    obj = query.join(contract_q, m.AlarmTrack.contract_id==contract_q.c.id)
    obj = obj.order_by(desc(contract_q.c.resource_id))
    obj = obj.order_by(desc(contract_q.c.project_id)).all()
    
    
    if not obj:
        raise exc.NotFoundException()
    return obj

########################


def failure_track_get_all(start_date, end_date):
    query = model_query(m.FailureTrack)
    if start_date:
        query = query.filter(m.FailureTrack.created_at >= start_date)
    if end_date:
        query = query.filter(m.FailureTrack.created_at <= end_date)

    return query.all()


def failure_track_create(values):
    session = get_session()
    with session.begin():
        failure = m.FailureTrack()
        failure.update(values.copy())

        try:
            failure.save(session)
        except db_exc.DBDuplicateEntry as e:
            raise exc.DBDuplicateEntry("Duplicate entry for failure track: %s"
                                       % e.columns)

        return failure


########################
