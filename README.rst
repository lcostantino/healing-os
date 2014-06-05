===============================
healing
===============================

healing

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/healing
* Source: http://git.openstack.org/cgit/openstack/healing
* Bugs: http://bugs.launchpad.net/healing

Notes
-------
It run a single worker, so use a production wsgi servier (gunicorn,
etc) to server multiple requests. Right now command execution
is not in a different worker and we use block calls from os-clients.

Features
--------




