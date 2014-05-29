#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import eventlet

eventlet.monkey_patch(
    os=True,
    select=True,
    socket=True,
    thread=False if '--use-debugger' in sys.argv else True,
    time=True)

import os

POSSIBLE_TOPDIR = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                   os.pardir,
                                   os.pardir))
if os.path.exists(os.path.join(POSSIBLE_TOPDIR, 'healing', '__init__.py')):
    sys.path.insert(0, POSSIBLE_TOPDIR)

#from oslo import messaging
from oslo.config import cfg

from healing import config
from healing.api import app
from wsgiref import simple_server
from healing.openstack.common import log as logging


LOG = logging.getLogger(__name__)


#from mistral
def launch_api(transport):
    host = cfg.CONF.api.host
    port = cfg.CONF.api.port
    server = simple_server.make_server(host, port,
                                       app.setup_app(transport=transport))
    LOG.info("Healing API is serving on http://%s:%s (PID=%s)" %
             (host, port, os.getpid()))
    server.serve_forever()


def launch_any(transport, options):
    # Launch the servers on different threads.
    threads = [eventlet.spawn(LAUNCH_OPTIONS[option], transport)
               for option in options]
    [thread.wait() for thread in threads]


def create_db():
    from healing.db.sqlalchemy.api import setup_db
    setup_db()
    
# Map cli options to appropriate functions. The cli options are
# registered in healing config.py.
LAUNCH_OPTIONS = {
    'api': launch_api,
    'db': create_db,
}


def main():
    try:
        config.parse_args()
        logging.setup('Healing')

        # Please refer to the oslo.messaging documentation for transport
        # configuration. The default transport for oslo.messaging is
        # rabbitMQ. The available transport drivers are listed in the
        # setup.cfg file in oslo.messaging under the entry_points section for
        # oslo.messaging.drivers. The transport driver is specified using the
        # rpc_backend option in the default section of the oslo configuration
        # file. The expected value for the rpc_backend is one of the key
        # values available for the oslo.messaging.drivers (i.e. rabbit, fake).
        # There are additional options such as ssl and credential that can be
        # specified depending on the driver.  Please refer to the driver
        # implementation for those additional options. It's important to note
        # that the "fake" transport should only be used if "all" the Mistral
        # servers are launched on the same process. Otherwise, messages do not
        # get delivered if the Mistral servers are launched on different
        # processes because the "fake" transport is using an in process queue.
        #transport = messaging.get_transport(cfg.CONF)
        transport = None
        try:
            create_db()
        except Exception as e:
            print e
            pass
        launch_api(transport)
    except RuntimeError, e:
        sys.stderr.write("ERROR: %s\n" % e)
        sys.exit(1)


if __name__ == '__main__':
    main()