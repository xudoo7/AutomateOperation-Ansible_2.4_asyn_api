# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from __future__ import absolute_import
from app import celery
from models.ansible_api import ANSRunner
from app.utilites import pb_prepare
from config import BaseConfig
import logconfig, logging

logconfig.init_logging(BaseConfig.APP_LOG_DIR)
logger = logging.getLogger('myapp')

@celery.task
def add_together(a=1, b=2):
    print("vars: ",a,b)
    return a + b


@celery.task(bind=True)
def callansibleRun(self,resource):
    import traceback
    try:
        inventory = resource.pop('resource')
    except KeyError:
        print(traceback.print_exc())
        logger.warning("resource missing iventory attributes!!!")
    ansibleRun = ANSRunner(inventory)
    ansibleRun.run_model(**resource)
    return ansibleRun.get_model_result(self.request.id)

@celery.task(bind=True)
def callansiblePlookbook(self, resource):
    try:
        inventory = resource.pop('resource')
        playbook_info = resource.pop('playbook')
        pb_prepare(**playbook_info)
    except KeyError:
        inventory = None
        playbook_info = None
        logger.warning('resource missing inventory or playbook attributes!!!')

    ansiblePlaybook = ANSRunner(inventory)
    ansiblePlaybook.run_playbook(**playbook_info)
    return ansiblePlaybook.get_playbook_result(self.request.id)

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
