# -*- coding: utf-8 -*-
#
# Copyright 2014 - Intel, Inc.
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

"""
Configuration options registration and useful routines.
"""

from oslo.config import cfg
from keystoneclient.middleware import auth_token

from healing.openstack.common import log
from healing.openstack.common import memorycache
from healing import version


api_opts = [
    cfg.StrOpt('host', default='0.0.0.0', help='Healing API server host'),
    cfg.BoolOpt('use_cherrypy', default=False, help='Start a cherrypy wsgi server'),
    cfg.IntOpt('port', default=9191, help='Healing API server port'),
    cfg.StrOpt('alarm_handler_url', default="log://", help='Default Alarm Handler callback'),
    cfg.ListOpt('unauthorized_urls', default=[], help=
                'Do not check keystone token for urls'),
]

pecan_opts = [
    cfg.StrOpt('root', default='healing.api.controllers.root.RootController',
               help='Pecan root controller'),
    cfg.ListOpt('modules', default=["healing.api"]),
    cfg.BoolOpt('debug', default=False),
    cfg.BoolOpt('auth_enable', default=True)
]

plugin_opts = [
    cfg.StrOpt('plugins_config_file',
               default="plugins_config.yaml",
               help="plugins config file."),
]

action_executor_opts = [
    cfg.StrOpt('manager',
               default='actionexecutor.manager.ActionManager'),
    cfg.StrOpt('topic',
               default='action_topic'),
    cfg.IntOpt('workers', default=2),
    cfg.BoolOpt('periodic_enable', default=False),
    cfg.IntOpt('task_period', default=60),
    
]
action_opts = [
    cfg.StrOpt('host',
               help="Hostname"),
]

db_opts = []


CONF = cfg.CONF

CONF.register_opts(api_opts, group='api')
CONF.register_opts(pecan_opts, group='pecan')
CONF.register_opts(auth_token.opts, group='keystone')
CONF.register_opts(db_opts, group='database')
CONF.register_opts(plugin_opts, group='plugins')
CONF.register_opts(action_executor_opts, group='action_executor')
CONF.register_opts(action_opts)
CONF.register_cli_opts([cfg.StrOpt('server', default='api',
                        help='for launch.py')])

CONF.import_opt('verbose', 'healing.openstack.common.log')
CONF.import_opt('debug', 'healing.openstack.common.log')
CONF.import_opt('log_dir', 'healing.openstack.common.log')
CONF.import_opt('log_file', 'healing.openstack.common.log')
CONF.import_opt('log_config_append', 'healing.openstack.common.log')
CONF.import_opt('log_format', 'healing.openstack.common.log')
CONF.import_opt('log_date_format', 'healing.openstack.common.log')
CONF.import_opt('use_syslog', 'healing.openstack.common.log')
CONF.import_opt('syslog_log_facility', 'healing.openstack.common.log')

cfg.set_defaults(log.log_opts,
                 default_log_levels=['sqlalchemy=WARN',
                                     'eventlet.wsgi.server=WARN'])


def parse_args(args=None, usage=None, default_config_files=None):
    CONF(args=args,
         project='healing',
         version=version,
         usage=usage,
         default_config_files=default_config_files)


def get_config():
    return CONF
