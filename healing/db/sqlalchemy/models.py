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
    source = sa.Column(sa.String(40))
    status = sa.Column(sa.String(20), nullable=True, default='init')
    action_meta = sa.Column(sa.String(200), nullable=True)
    target_id = sa.Column(sa.String(80))
    project_id = sa.Column(sa.String(80), nullable=True)
    internal_data = sa.Column(sa.String(200), nullable=True)



