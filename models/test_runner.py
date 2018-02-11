# -*- coding: utf-8 -*-

#from models.runner import AdHocRunner, CommandRunner, PlayBookRunner
from runner import AdHocRunner, CommandRunner, PlayBookRunner
#from models.inventory import BaseInventory
from inventory import BaseInventory
import json


def  TestAdHocRunner():
        """
         以yml的形式 执行多个命令
        :return:
        """

        host_data = [
            {
                "hostname": "localhost",
                "ip": "192.168.213.129",
                "port": 22,
                "username": "root",
                "password": "root!2013",
            },
        ]
        res = [{'hostsname': '127.0.0.1', 'ip': '127.0.0.1', 'username': 'root', 'port': '22', 'password': 'root!2013'}]
        #inventory = BaseInventory(host_data)
        runner = AdHocRunner(res)

        #tasks = [
        #    {"action": {"module": "shell", "args": "whoami"}, "name": "run_whoami"},
        #]
        #ret = runner.run('all', 'shell', 'whoami')
        ret = runner.run('all', 'shell', 'w')
        print(ret.results_summary)
        print(ret.results_raw)


def TestCommandRunner():
        """
        执行单个命令，返回结果
        :return:
        """

        host_data = [
            {
                "hostname": "localhost",
                "ip": "152.55.249.20",
                "port": 22,
                "username": "root",
                "password": "test!2013",
            },
        ]
        #xx=[{'ip': '127.0.0.1', 'hostname': 'localhost', 'username': 'root', 'password': 'root!2013', 'port': '22', 'groups': ['group1'], 'vars': {'var1': 'xxxx', 'var2': 'yyy'}}]
        runner = CommandRunner(host_data)


        res = runner.execute('pwd', 'all')
        print(res.results_command)
        print(res.results_raw)
        print(res.results_command['localhost']['stdout'])


def TestPlayBookRunner():
        host_list = [{
            "hostname": "testserver1",
            "ip": "102.1.1.1",
            "port": 22,
            "username": "root",
            "password": "password",
            "private_key": "/tmp/private_key",
            "become": {
                "method": "sudo",
                "user": "root",
                "pass": None,
            },
            "groups": ["group1", "group2"],
            "vars": {"sexy": "yes"},
        }, {
            "hostname": "testserver2",
            "ip": "127.0.0.1",
            "port": 22,
            "username": "root",
            "password": "password",
            "private_key": "/tmp/private_key",
            "become": {
                "method": "su",
                "user": "root",
                "pass": "123",
            },
            "groups": ["group3", "group4"],
            "vars": {"love": "yes"},
        }]
        xx=[{'ip': '127.0.0.1', 'hostname': 'localhost', 'username': 'root', 'password': 'root!2013', 'port': '22', 'groups': ['group1'], 'vars': {'var1': 'xxxx', 'var2': 'yyy'}}]
        runner = PlayBookRunner(xx)
        res = runner.run("xx.yaml", "host")
        #print(res.item_results)
        #for key in res.keys():
        #   print(key)
        for value in res.values():
            print(json.dumps(value))
 #       print((res['plays'][0]['tasks'][1]))
#        print(res['stats']['localhost'])


if __name__ == "__main__":
    TestAdHocRunner()
#    TestCommandRunner()
#    TestPlayBookRunner()
