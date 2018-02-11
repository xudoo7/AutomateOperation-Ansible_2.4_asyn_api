import os

basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig(object):
    CELERY_BROKER_URL = 'amqp://myuser:mypassword@192.168.56.102:5672/myvhost'
    #CELERY_BROKER_URL = 'amqp://guest@localhost:5672//'
    CELERY_RESULT_BACKEND = 'amqp://myuser:mypassword@192.168.56.102:5672/myvhost'
    #CELERY_RESULT_BACKEND = 'amqp://guest@localhost:5672//'
    CELERY_TASK_SERIALIZER = 'json'
    #CELERY_IMPORTS = ('app.tasks.CeleryAnsibleCall')
    APP_LOG_DIR = os.path.join(basedir, 'logs')
    PLAYBOOK_SERVER = 'http://192.168.213.129:5000/playbooks'
    PLAYBOOK_DIR = os.path.join(basedir, 'playbooks')
    TEMPLATE_SERVER = 'http://192.168.213.129:5000/templates'
    TEMPLATE_DIR = os.path.join(basedir, 'templates')

class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')

config = {
    'testing': TestingConfig,
    'default': BaseConfig
}
