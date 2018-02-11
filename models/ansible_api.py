# -*- coding=utf-8 -*-
from __future__ import print_function, unicode_literals, absolute_import
import json,sys,os
from ansible import constants
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.inventory.host import Host,Group
from config import BaseConfig

class MyInventory():
    """
    this is ansible inventory object.
    """
    def __init__(self, resource):
        self.resource = resource
        self.loader = DataLoader()
        self.inventory = InventoryManager(loader=self.loader, sources=['/etc/ansible/hosts'])
        #self.inventory = InventoryManager(loader=self.loader, sources=self.resource)
        #self.variable_manager.set_inventory(self.inventory)
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)
        self.dynamic_inventory()

    def add_dynamic_group(self, hosts, groupname, groupvars=None):
        """add new hosts to a group"""
        self.inventory.add_group(groupname)
        my_group = Group(name=groupname)

        # if group variables exists, add them to group
        if groupvars:
            for key in groupvars:
                my_group.set_variable(key, groupvars[key])

        # add hosts to group
        #print(hosts)
        for host in hosts:
            # set connection variables
            hostname = host.get("hostname")
            hostip = host.get('ip', hostname)
            hostport = host.get("port")
            username = host.get("username")
            password = host.get("password")
            ssh_key = host.get("ssh_key")
            my_host = Host(name=hostname, port=hostport)
            self.variable_manager.set_host_variable(host=my_host, varname='ansible_ssh_host', value=hostip)
            self.variable_manager.set_host_variable(host=my_host, varname='ansible_ssh_pass', value=password)
            self.variable_manager.set_host_variable(host=my_host, varname='ansible_ssh_port', value=hostport)
            self.variable_manager.set_host_variable(host=my_host, varname='ansible_ssh_user', value=username)
            self.variable_manager.set_host_variable(host=my_host, varname='ansible_ssh_private_key_file', value=ssh_key)
            # my_host.set_variable('ansible_ssh_pass', password)
            # my_host.set_variable('ansible_ssh_private_key_file', ssh_key)

            # set other variables
            #print(host)
            for key in host:
                if key not in ["hostname", "port", "username", "password"]:
                    self.variable_manager.set_host_variable(host=my_host, varname=key, value=host[key])

            # add to group
            self.inventory.add_host(host=hostname, group=groupname, port=hostport)
            #ghost = Host(name="192.168.8.119")

    def dynamic_inventory(self):
        """
            add new hosts to inventory.
        """
        if isinstance(self.resource, list):
            self.add_dynamic_group(self.resource, 'default_group')
        elif isinstance(self.resource, dict):
            for groupname in self.resource:
                #print(groupname)
                self.add_dynamic_group(self.resource[groupname].get("hosts"), groupname, self.resource[groupname].get("vars"))

class ModelResultsCollector(CallbackBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        self.host_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result,  *args, **kwargs):
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result,  *args, **kwargs):
        self.host_failed[result._host.get_name()] = result

class PlayBookResultsCollector(CallbackBase):
    CALLBACK_VERSION = 2.0
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_ok = {}
        self.task_skipped = {}
        self.task_failed = {}
        self.task_status = {}
        self.task_unreachable = {}

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.task_ok[result._host.get_name()]  = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.task_failed[result._host.get_name()] = result

    def v2_runner_on_unreachable(self, result):
        self.task_unreachable[result._host.get_name()] = result

    def v2_runner_on_skipped(self, result):
        self.task_ok[result._host.get_name()]  = result

    def v2_playbook_on_stats(self, stats):
        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)
            self.task_status[h] = {
                                       "ok":t['ok'],
                                       "changed" : t['changed'],
                                       "unreachable":t['unreachable'],
                                       "skipped":t['skipped'],
                                       "failed":t['failures']
                                   }

class ANSRunner(object):
    """
    This is a General object for parallel execute modules.
    """
    def __init__(self, resource, *args, **kwargs):
        self.resource = resource
        self.inventory = None
        self.variable_manager = None
        self.loader = None
        self.options = None
        self.passwords = None
        self.callback = None
        self.__initializeData()
        self.results_raw = {}

    def __initializeData(self):
        """ 初始化ansible """
        Options = namedtuple('Options', ['connection','module_path', 'forks', 'timeout',  'remote_user',
                'ask_pass', 'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
                'scp_extra_args', 'become', 'become_method', 'become_user', 'ask_value_pass', 'verbosity',
                'check', 'listhosts', 'listtasks', 'listtags', 'syntax','diff'])

        self.loader = DataLoader()
        self.options = Options(connection='smart', module_path=None, forks=100, timeout=10,
                remote_user='root', ask_pass=False, private_key_file=None, ssh_common_args=None, ssh_extra_args=None,
                sftp_extra_args=None, scp_extra_args=None, become=None, become_method=None,
                become_user='root', ask_value_pass=False, verbosity=None, check=False, listhosts=False,
                listtasks=False, listtags=False, syntax=False, diff=True)

        self.passwords = dict(sshpass=None, becomepass=None)
        my_inventory = MyInventory(self.resource)
        self.inventory = my_inventory.inventory
        self.variable_manager = my_inventory.variable_manager

        # self.variable_manager.set_inventory(self.inventory)
        # self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)

    def run_model(self, host_list, module_name, module_args):
        """
        run module from andible ad-hoc.
        module_name: ansible module_name
        module_args: ansible module args
        """
        print(host_list)
        play_source = dict(
                name="Ansible Play",
                hosts=host_list,
                gather_facts='no',
                tasks=[dict(action=dict(module=module_name, args=module_args))]
        )

        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)
        tqm = None
        # if self.redisKey:self.callback = ModelResultsCollectorToSave(self.redisKey,self.logId)
        # else:self.callback = ModelResultsCollector()
        self.callback = ModelResultsCollector()
        import traceback
        try:
            tqm = TaskQueueManager(
                    inventory=self.inventory,
                    variable_manager=self.variable_manager,
                    loader=self.loader,
                    options=self.options,
                    passwords=self.passwords,
                    stdout_callback="minimal",
            )
            tqm._stdout_callback = self.callback
            tqm.run(play)
        except Exception as err:
            print(traceback.print_exc())
            # DsRedis.OpsAnsibleModel.lpush(self.redisKey,data=err)
            # if self.logId:AnsibleSaveResult.Model.insert(self.logId, err)
        finally:
            if tqm is not None:
                tqm.cleanup()

    def run_playbook(self, pb_name=None, pb_type=None, *args, **kwargs):
        """
        run ansible palybook
        """
        try:
            # if self.redisKey:self.callback = PlayBookResultsCollectorToSave(self.redisKey,self.logId)
            self.callback = PlayBookResultsCollector()
            playbook_type = os.path.join('/root/PycharmProjects/ansible_2.4_asyn_api/playbooks', pb_type)
            playbook_path = os.path.join(playbook_type, pb_name)
            print(playbook_path)
            executor = PlaybookExecutor(
                playbooks=[playbook_path],
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords
            )
            executor._tqm._stdout_callback = self.callback
            #constants.HOST_KEY_CHECKING = False #关闭第一次使用ansible连接客户端是输入命令
            executor.run()
        except Exception as err:
            return False

    def get_model_result(self, task_id):
        self.results_raw = {'jid:': task_id, 'success':{}, 'failed':{}, 'unreachable':{}}
        for host, result in self.callback.host_ok.items():
            hostvisiable = host.replace('.','_')
            self.results_raw['success'][hostvisiable] = result._result

        for host, result in self.callback.host_failed.items():
            hostvisiable = host.replace('.','_')
            self.results_raw['failed'][hostvisiable] = result._result

        for host, result in self.callback.host_unreachable.items():
            hostvisiable = host.replace('.','_')
            self.results_raw['unreachable'][hostvisiable]= result._result

        return json.dumps(self.results_raw)
        #print(self.results_raw)
        #return self.results_raw

    def get_playbook_result(self, task_id):
        #self.results_raw = {'jid:': task_id, 'skipped':{}, 'failed':{}, 'ok':{}, "status":{}, 'unreachable':{}, "changed":{}}
        self.results_raw = {'jid:': task_id, 'skipped':{}, 'failed':{}, 'ok':{}, "status":{}, 'unreachable':{}}
        for host, result in self.callback.task_ok.items():
            self.results_raw['ok'][host] = result

        for host, result in self.callback.task_failed.items():
            self.results_raw['failed'][host] = result

        for host, result in self.callback.task_status.items():
            self.results_raw['status'][host] = result

        #for host, result in self.callback.task_changed.items():
        #     self.results_raw['changed'][host] = result

        for host, result in self.callback.task_skipped.items():
            self.results_raw['skipped'][host] = result

        for host, result in self.callback.task_unreachable.items():
            self.results_raw['unreachable'][host] = result
        #print(self.results_raw)
        return self.results_raw


if __name__ == '__main__':
    # resource = [ #列表形式
    #              {"hostname": "192.168.8.119"},
    #              # {"hostname": "192.168.6.43"},
    #              # {"hostname": "192.168.1.233"},
    #              ]
    resource = { #字典形式
                    "dynamic_host": {
                        "hosts": [
                                    {'username': 'root', 'password': 'root!2013', 'ip': '127.0.0.1', 'hostname': '127.0.0.1', 'port':'22'},
                                  ],
                        "vars": {
                                 "var1":"ansible",
                                 "var2":"saltstack"
                                 }
                    }
               }
    res = {"dynamic_host": { "hosts": [{"hostname": "127.0.0.1", "ip": "127.0.0.1", "username": "root", "port": "22", "password": "root!2013"}], "vars": {"var1": "ansible", "var2": "saltstack"}}}
    xx = [{"hostname": "127.0.0.1", "ip": "127.0.0.1", "username": "root", "port": "22", "password": "root!2013"}]
    rbt = ANSRunner(resource)
    # Ansible Adhoc
    #rbt.run_model(host_list=["127.0.0.1"], module_name='shell', module_args="uptime")
    #print(rbt.get_model_result('001'))
    #print(data)
    # Ansible playbook
    rbt.run_playbook('xx.yaml', 'host')
    print(rbt.get_playbook_result('002'))
    # rbt.run_model(host_list=[],module_name='yum',module_args="name=htop state=present")
