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

from oslo.config import cfg

from healing.api import access_control
from healing import config
from healing.api import hooks
from healing.api import middleware
from healing.db import api as db_api


def get_pecan_config():
    # Set up the pecan configuration.
    opts = cfg.CONF.pecan

    cfg_dict = {
        "app": {
            "root": opts.root,
            "modules": opts.modules,
            "debug": opts.debug,
            "auth_enable": opts.auth_enable
        }
    }

    return pecan.configuration.conf_from_dict(cfg_dict)


def setup_app(pecan_config=None, transport=None):
    if not pecan_config:
        pecan_config = get_pecan_config()

    #TODO; pasar db hook?
    app_hooks = [hooks.ConfigHook(),
                 hooks.TranslationHook(),
                 hooks.CustomErrorHook(),
                 ]
    #if config.CONF.pecan.auth_enable:
    app_hooks.append(access_control.DelayedAuthHook())

    app_conf = dict(pecan_config.app)

    db_api.setup_db()

    app = pecan.make_app(
        app_conf.pop('root'),
        hooks=app_hooks,
        logging=getattr(config, 'logging', {}),
        wrap_app=middleware.ParsableErrorMiddleware,
        guess_content_type_from_ext=False,
        **app_conf
    )

    # Set up access control.
    app = access_control.setup(app)

    return app
