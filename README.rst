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


Execute
----------

 API)	4 python healing/cmd/launch.py --server api --config-file etc/healing.conf.example
 Action)	$ python healing/cmd/launch.py --server action --config-file etc/healing.conf.example

Develop Install
---------------
 $ python setup.py develop 
 
 If you have issues check your setupttool version. 
 Also try:
   #apt-get remove python-setuptools  
   #apt-get install python-setuptools        


Description
------------


Notes
-----------
We used Mistral for API reference implementation as well taken the
best of other components like Nova objects.


