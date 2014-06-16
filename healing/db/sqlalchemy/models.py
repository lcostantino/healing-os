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

import sqlalchemy as sa
import uuid

from healing.db.sqlalchemy import model_base as mb

## Helpers

#TODO: i think oslo has uuid utils, replace here!


def _generate_unicode_uuid():
    return unicode(str(uuid.uuid4()))


def _id_column():
    return sa.Column(sa.String(36),
                     primary_key=True,
                     default=_generate_unicode_uuid)


class Action(mb.HealingBase):
    """Contains info about actions."""

    __tablename__ = 'actions'

    __table_args__ = (
        sa.UniqueConstraint('id'),
    )

    id = _id_column()
    name = sa.Column(sa.String(80))
    status = sa.Column(sa.String(20), nullable=True, default='init')
    action_meta = sa.Column(sa.String(200), nullable=True)
    target_id = sa.Column(sa.String(80))
    project_id = sa.Column(sa.String(80), nullable=True)
    request_id = sa.Column(sa.String(80), nullable=True)
    internal_data = sa.Column(sa.String(200), nullable=True)
    output = sa.Column(sa.Text(), nullable=True)

class SLAContract(mb.HealingBase):
    """Contains info about the SLA contracts."""

    __tablename__ = 'sla_contract'

    __table_args__ = (
        sa.UniqueConstraint('id'),
    )

    id = _id_column()
    project_id = sa.Column(sa.String(80), nullable=True)
    type = sa.Column(sa.String(255), nullable=True)
    value = sa.Column(sa.String(255), nullable=True)
    name = sa.Column(sa.String(255), nullable=True)
    action = sa.Column(sa.String(255), nullable=True)
    resource_id = sa.Column(sa.String(255), nullable=True)
    action_options = sa.Column(sa.String(255), nullable=True)
    
    
class AlarmTrack(mb.HealingBase):
    """Contains info about the ALARMs."""

    __tablename__ = 'alarm_track'

    __table_args__ = (
        sa.UniqueConstraint('id'),
    )

    id = _id_column()
    alarm_id = sa.Column(sa.String(80))
    contract_id = sa.Column(sa.String(80))
    type = sa.Column(sa.String(100))
    meter = sa.Column(sa.String(100))
    threshold = sa.Column(sa.String(20))
    operator = sa.Column(sa.String(5))
    period = sa.Column(sa.Integer(), default=10)
    evaluation_period = sa.Column(sa.Integer(), default=1)
    name = sa.Column(sa.String(255))
    query = sa.Column(sa.String(255))
    statistic = sa.Column(sa.String(255))
    # if not tru SLA
    action = sa.Column(sa.String(255))


class FailureTrack(mb.HealingBase):
    """Contains info about the SLA contracts."""

    __tablename__ = 'failure_track'

    __table_args__ = (
        sa.UniqueConstraint('id'),
    )

    id = _id_column()
    alarm_id = sa.Column(sa.String(255))
    data = sa.Column(sa.String(255), nullable=True)
    contract_names = sa.Column(sa.String(255), nullable=True)
