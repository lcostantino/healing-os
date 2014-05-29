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


def to_dict(func):
    def decorator(*args, **kwargs):
        res = func(*args, **kwargs)

        if isinstance(res, list):
            return [item.to_dict() for item in res]

        if res:
            return res.to_dict()
        else:
            return None

    return decorator


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


#TODO: pasar a objetos... remover to_dict
@to_dict
def action_create(values):
    #TODO: move to @session_aware
    session = get_session()
    with session.begin():
        action = m.Action()
        action.update(values.copy())

        try:
            action.save(session=get_session())
        except db_exc.DBDuplicateEntry as e:
            raise exc.DBDuplicateEntry("Duplicate entry for Action: %s"
                                       % e.columns)

        return action

#TODO: remove to_dict when we implement field coercion
@to_dict
def action_update(action_id, values):
    session = get_session()
    with session.begin():
        action = _action_get(action_id)
        if not action:
            raise exc.NotFoundException("action not found [action_id=%s]" %
                                        action_id)

        action.update(values.copy())

        return action


def action_delete(action_id):
    session = get_session()
    with session.begin():
        res = model_query(m.Action, session=session).filter_by(id=action_id)\
                                                    .delete()
        if not res:
            raise exc.NotFoundException("Action not found [action_id=%s]" %
                                        action_id)


@to_dict
def action_get(action_id):
    return _action_get(action_id)


@to_dict
def actions_get_all(filters=None):
    if not filters:
        filters = {}
    return _actions_get_all(filters)


def _actions_get_all(filters, order='-created_at'):
    query = model_query(m.Action)
    return query.filter_by(**filters).order_by(order).all()


def action_get_by_filter(filters, updated_time_gt=None, order='-created_at'):
    """
    :param updated_time_gt: if set, will do updated_at > updated_time_gt
    """
    query = model_query(m.Action)
    query = query.filter_by(**filters)
    if updated_time_gt:
        query = query.filter((m.Action.updated_at >= updated_time_gt) |
                             (m.Action.create_at >= updated_time_gt))
    result = query.order_by(order).first()
    if not result:
        raise exc.NotFoundException()
    return result

#TODO: move exception to db/api.py? may be much better to abstract
def _action_get(action_id):
    query = model_query(m.Action)
    obj = query.filter_by(id=action_id).first()
    if not obj:
        raise exc.NotFoundException()
    return obj

#setup_db()