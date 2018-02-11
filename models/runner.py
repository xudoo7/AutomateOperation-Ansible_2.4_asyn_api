# ~*~ coding: utf-8 ~*~
from __future__ import print_function, unicode_literals, absolute_import
import os
from collections import namedtuple

from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.playbook.play import Play
import ansible.constants as C

from models.callback import AdHocResultCallback, PlaybookResultCallBack, CommandResultCallback
from models.inventory import BaseInventory
from models.exceptions import AnsibleError
#import models.exceptions
from app.utilites import handle_exception
from config import BaseConfig


__all__ = ["AdHocRunner", "PlayBookRunner"]
C.HOST_KEY_CHECKING = False
passwords = dict(sshpass=None, becomepass=None)



#Options = namedtuple('Options', [
#    'listtags', 'listtasks', 'listhosts', 'syntax', 'connection',
#    'module_path', 'forks', 'remote_user', 'private_key_file', 'timeout',
#    'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
#    'scp_extra_args', 'become', 'become_method', 'become_user',
#    'verbosity', 'check', 'extra_vars',
#    'diff', 'gathering', 'remote_tmp',
#])
Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user', 'check', 'diff', 'listhosts', 'listtasks', 'listtags', 'syntax'])


def get_default_options():
#    options = Options(
#        listtags=False,
#        listtasks=False,
#        listhosts=False,
#        syntax=False,
#        timeout=60,
#        connection='smart',
#        module_path='/usr/local/lib/python3.6/site-packages/ansible/modules/',
#        forks=10,
#        remote_user='root',
#        private_key_file=None,
#        ssh_common_args="",
#        ssh_extra_args="",
#        sftp_extra_args="",
#        scp_extra_args="",
#        become=None,
#        become_method=None,
#        become_user=None,
#        verbosity=None,
#        extra_vars=[],
#        check=False,
#        playbook_path='/tmp/xxx.yaml',
#        passwords='test!2013',
#        diff=False,
#        gathering='implicit',
#        remote_tmp='/tmp/.ansible'
#    )
    options = Options(connection='local', module_path='/usr/local/lib/python3.6/site-packages/ansible/modules/', forks=100, become=None, become_method=None, become_user=None, check=False, diff=False, listhosts=False, listtasks=False, listtags=False, syntax=False)
    return options


# Jumpserver not use playbook
class PlayBookRunner():
    """
    用于执行AnsiblePlaybook的接口.简化Playbook对象的使用.
    """

    # Default results callback
    results_callback_class = PlaybookResultCallBack
    loader_class = DataLoader
    variable_manager_class = VariableManager
    options = get_default_options()

    def __init__(self, host_list=None, *args, **kwargs):
        """
        :param options: Ansible options like ansible.cfg
        :param inventory: Ansible inventory
        """

        self.options = get_default_options()
        C.RETRY_FILES_ENABLED = False
        #self.resource = host_list
        #BaseInventory(self.resource)
        self.loader = self.loader_class()
        self.inventory = BaseInventory(host_list)
        #self.inventory = InventoryManager(loader=self.loader, sources=self.resource)
        self.results_callback = self.results_callback_class()
        #self.playbook_path = playbook_path
        self.variable_manager = self.variable_manager_class(
            loader=self.loader, inventory=self.inventory
        )
        self.passwords = passwords
        self.__check()

    def __check(self):
        if not self.inventory.list_hosts('all'):
            print(self.inventory.list_hosts('all'))
            raise AnsibleError('Inventory is empty')

    def run(self, pb_name=None, pb_type=None, *args, **kwargs):
        playbook_type = os.path.join(BaseConfig.PLAYBOOK_DIR, pb_type)
        playbook_path = os.path.join(playbook_type, pb_name)
        executor = PlaybookExecutor(
            playbooks=[playbook_path],
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=self.loader,
            options=self.options,
            passwords=self.passwords
        )

        if executor._tqm:
            executor._tqm._stdout_callback = self.results_callback
        executor.run()
        executor._tqm.cleanup()
        return self.results_callback.output



class AdHocRunner:
    """
    ADHoc Runner接口
    """
    results_callback_class = AdHocResultCallback
    loader_class = DataLoader
    variable_manager_class = VariableManager
    options = get_default_options()
    default_options = get_default_options()

    def __init__(self, host_data, *args, **kwargs):
        #self.options = options
        self.inventory = BaseInventory(host_data)
        self.loader = self.loader_class()
        #self.passwords = self.inventory.host['hostname']
        #self.loader = DataLoader()
        self.variable_manager = VariableManager(
            loader=self.loader, inventory=self.inventory
        )
        self.results_raw = {}
        self.passwords = passwords

    @staticmethod
    def check_module_args(module_name, module_args=''):
        if module_name in C.MODULE_REQUIRE_ARGS and not module_args:
            err = "No argument passed to '%s' module." % module_name
            raise AnsibleError(err)

    def check_pattern(self, pattern):
        if not pattern:
            raise AnsibleError("Pattern `{}` is not valid!".format(pattern))
        if not self.inventory.list_hosts("all"):
            raise AnsibleError("Inventory is empty.")
        if not self.inventory.list_hosts(pattern):
            raise AnsibleError(
                "pattern: %s  dose not match any hosts." % pattern
            )

    def clean_tasks(self, tasks):
        cleaned_tasks = []
        for task in tasks:
            self.check_module_args(task['action']['module'], task['action'].get('args'))
            cleaned_tasks.append(task)
        return cleaned_tasks

    def set_option(self, k, v):
        kwargs = {k: v}
        self.options = self.options._replace(**kwargs)

    def test_var_args_call(self, host_list, module_name, module_args):
         print("host_list:", host_list)
         print("module_name:", module_name)
         print("module_args:", module_args)
         print(self.passwords)

    #def run(self, tasks, pattern, play_name='Ansible Ad-hoc', gather_facts='no'):
    def run(self, host_list=None, module_name=None, module_args=None, *args, **kwargs):
        """
        :param tasks: [{'action': {'module': 'shell', 'args': 'ls'}, ...}, ]
        :param pattern: all, *, or othersl
        :param play_name: The play name
        :return:
        """
        #self.check_pattern('all')
        results_callback = self.results_callback_class()
        #tasks = [dict(action=dict(module=module_name, args=module_args))]
        #cleaned_tasks = self.clean_tasks(tasks)

        play_source = dict(
            name="Ansible Play",
            hosts=host_list,
            gather_facts='no',
            #tasks=cleaned_tasks
            tasks=[dict(action=dict(module=module_name, args=module_args))]
        )

        play = Play().load(
            play_source,
            variable_manager=self.variable_manager,
            loader=self.loader,
        )

        tqm = TaskQueueManager(
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=self.loader,
            options=self.options,
            stdout_callback=results_callback,
            passwords=self.passwords,
        )

#        tqm.run(play)
#       return results_callback
        try:
            tqm.run(play)
            #print(results_callback)
            return results_callback

        except Exception as e:
            raise AnsibleError(e)
        finally:
            tqm.cleanup()
            self.loader.cleanup_all_tmp_files()

    def get_result(self, task_id):
        if handle_exception(self.results_raw):
            return self.results_raw
        self.results_raw = {'jid:': task_id, 'success': {}, 'failed': {}, 'unreachable': {}}
        for host, result in self.callback.host_unreachable.items():
            self.results_raw['unreachable'][host] = result._result['msg']

        for host, result in self.callback.host_failed.items():
            try:

                self.results_raw['failed'][host] = result._result['msg']
            except KeyError:
                self.results_raw['failed'][host] = 'Command executed Error!'

        for host, result in self.callback.host_ok.items():
            self.results_raw['success'][host] = result._result

        for host, result in self.callback.playbook_notify.items():
            self.results_raw['notify'][host] = result._result

        # logger.debug("Ansible exec result:%s" % self.results_raw)
        return self.results_raw


class CommandRunner(AdHocRunner):
    results_callback_class = CommandResultCallback
    modules_choices = ('shell', 'raw', 'command', 'script')

    def execute(self, cmd, pattern, module=None):
        if module and module not in self.modules_choices:
            raise AnsibleError("Module should in {}".format(self.modules_choices))
        else:
            module = "shell"

        tasks = [
            {"action": {"module": module, "args": cmd}}
        ]
        hosts = self.inventory.get_hosts(pattern=pattern)
        name = "Run command {} on {}".format(cmd, ", ".join([host.name for host in hosts]))
        return self.run(tasks, pattern, play_name=name)

