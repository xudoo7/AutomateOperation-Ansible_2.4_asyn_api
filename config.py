import os

basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig(object):
    CELERY_BROKER_URL = 'amqp://myuser:mypassword@192.168.213.130:5672/myvhost'
    CELERY_RESULT_BACKEND = 'amqp://myuser:mypassword@192.168.213.130:5672/myvhost'
    CELERY_TASK_SERIALIZER = 'json'
    APP_LOG_DIR = os.path.join(basedir, 'logs')
    INV_DIR = os.path.join(basedir, 'host')
    INV_SERVER = 'http://192.168.213.130/hosts'
    PLAYBOOK_SERVER = 'http://192.168.213.129/playbooks'
    PLAYBOOK_DIR = os.path.join(basedir, 'playbooks')
    TEMPLATE_SERVER = 'http://192.168.213.129/templates'
    TEMPLATE_DIR = os.path.join(basedir, 'templates')

class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')

config = {
    'testing': TestingConfig,
    'default': BaseConfig
}
