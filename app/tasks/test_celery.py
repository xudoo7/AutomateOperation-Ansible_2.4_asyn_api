# -*- coding: utf-8 -*-
from __future__ import absolute_import
from app.tasks.CeleryAnsibleCall import callansibleRun
from app import celery



res = {"data":{"host_list": "all",  "module_name": "shell", "module_args": "reboot", "resource": {"hostsname": "test1", "ip": "127.0.0.1", "username": "root", "port": "22", "password": "root!2013"}}}
xx=res.get('data')
print(xx)
rundelay=callansibleRun.delay(xx)
#rundelay.ready()
rundelay.get()