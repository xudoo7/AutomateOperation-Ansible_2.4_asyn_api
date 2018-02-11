# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from __future__ import absolute_import
from app import celery
from models.inventory import BaseInventory
#from models.runner import PlayBookRunner, AdHocRunner, CommandRunner
from models.ansible_api import ANSRunner
from app.utilites import pb_prepare
import json

@celery.task
def add_together(a=1, b=2):
    print("vars: ",a,b)
    return a + b


@celery.task(bind=True)
def callansibleRun(self,resource):
    res = resource.pop('resource')
    print(res)
    print(resource)
    #ansibleRun = AdHocRunner(res)
    #res = {"dynamic_host": { "hosts": [{"hostsname": "127.0.0.1", "ip": "127.0.0.1", "username": "root", "port": "22", "password": "root!2013"}], "vars": {"var1": "ansible", "var2": "saltstack"}}}
    ansibleRun = ANSRunner(res)
    ansibleRun.run_model(**resource)
    #ansibleRun.run_model(host_list=["127.0.0.1"], module_name='shell', module_args="uptime")
    #runResult = ansibleRun.run('all', 'shell', 'reboot')
    #print(runResult)
    #result = runResult.results_summary
    #print(runResult.results_summary)
    #print(runResult.results_raw)
    Result = ansibleRun.get_model_result(self.request.id)
    print(Result)
    return Result


@celery.task(bind=True)
def callansiblePlookbook(self, resource):
    try:
        inventory = resource.pop('resource')
        #print(inventory)
        playbook_info = resource.pop('playbook')
        #print(playbook_info)
        pb_prepare(**playbook_info)
    except KeyError:
        inventory = None
        playbook_info = None

    ansiblePlaybook = ANSRunner(inventory)
    #ansiblePlaybook.run()
    ansiblePlaybook.run_playbook(**playbook_info)
    runResult = ansiblePlaybook.get_playbook_result(self.request.id)
    return runResult

if __name__ == "__main__":
    '''
    cmd interface:
        res = {
       "resource":{
        "hosts": {
            "127.0.0.1": {"port": "22", "username": "xusd", "password": "xuderoo7"},
            },
        "groups": {
            "group1": {"hosts": ["127.0.0.1"], "vars": {'var1': 'xxxx', 'var2': 'yyy'}},
            },
        },
       "host_list": "127.0.0.1",
       "module_name": "shell",
       "module_args": "whoami",
       }

    playbook interface:
        res = {
       "resource":{
        "hosts": {
            "127.0.0.1": {"port": "22", "username": "xusd", "password": "xuderoo7"},
            },
        "groups": {
            "group1": {"hosts": ["127.0.0.1"], "vars": {'var1': 'xxxx', 'var2': 'yyy'}},
            },
        },
       "playbook": {
        "pb_type": "host",
        "pb_name": "cmd.yaml",
        },
       }
    '''
    """res = {
        "resource": {
            "hosts": {
                "127.0.0.1": {"port": "22", "username": "xusd", "password": "xuderoo7"},
            },
            "groups": {
                "group1": {"hosts": ["127.0.0.1"], "vars": {'var1': 'xxxx', 'var2': 'yyy'}},
            },
        },
        "playbook": {
            "pb_type": "host",
            "pb_name": "cmd.yaml",
        },
    }"""""
    res = {"data":{"host_list": "all",  "module_name": "shell", "module_args": "reboot", "resource": {"hostsname": "test1", "ip": "127.0.0.1", "username": "root", "port": "22", "password": "root!2013"}}}
    #rundelay=callansiblePlookbook.delay(res)
    #inventory = [res.pop('resource')]
    #print(inventory)
    xx=res.get('data')
    print(xx)
    def test_var_args_call(host_list, module_name, module_args):
         print("host_list:", host_list)
         print("module_name:", module_name)
         print("module_args:", module_args)
    #print(res)
    #test_var_args_call(**xx)
    rundelay=callansibleRun.delay(xx)
    rundelay.ready()
    print(rundelay.get())
    #print(rundelay)
