from unittest import TestCase
from wsgiref.simple_server import make_server
from dpt import testing as dpt

def server_runner(wsgi_app, global_conf, host=None, port=None):
    server = make_server(host, int(port), wsgi_app)
    server.serve_forever()

class Gateway(object):
    """Mobile gateway."""

    def __init__(self, parser, handler, receiver):
        self.parser = parser
        self.handler = handler
        self.receiver = receiver
        self._subscribers = {}

    def forward(self, receiver, text):
        assert receiver != self.receiver
        assert receiver in self._subscribers
        subscriber = self._subscribers[receiver]
        subscriber.receive(text)

    def send(self, subscriber, text):
        self._subscribers[subscriber.number] = subscriber
        message = self.parser(text)

        # record message
        from router.orm import Session
        session = Session()
        session.add(message)
        message.sender = subscriber.number
        message.receiver = self.receiver
        session.flush()
        session.refresh(message)

        response = self.handler(message)
        if response is not None:
            message.reply = response.unicode_body
            self.deliver(subscriber, response.body, message)

    def deliver(self, receiver, text, message):
        receiver.receive(text)

        # note delivery
        from router.orm import Session
        from router.models import Delivery
        session = Session()
        message.delivery = Delivery(time=message.time, message=message)
        session.flush()
        session.refresh(message)

class Subscriber(object):
    """Mobile subscriber."""

    def __init__(self, gateway, number=None):
        self.gateway = gateway
        self.number = number
        self._received = []

    def send(self, text):
        """Sends text to gateway."""

        text = text.lstrip("> ")
        self.gateway.send(self, text)

    def receive(self, text=None):
        if text is None:
            return self._received.pop(0)
        text = "<<< " + text
        self._received.append(text)

class FunctionalTestCase(TestCase):
    def setUp(self):
        from django.conf import settings
        settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                    }
                },
            INSTALLED_APPS=(
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'router',
                ),
            )
        from django.core.management import call_command
        call_command('syncdb', verbosity=0, interactive=False, database='default')
        super(FunctionalTestCase, self).setUp()

    def tearDown(self):
        super(FunctionalTestCase, self).tearDown()
        from django.core.management import call_command
        from django.db.models import get_apps
        from django.db.models import get_app
        from django.core.exceptions import ImproperlyConfigured

        # reset application data
        for app in get_apps():
            # waiting for http://code.djangoproject.com/ticket/3591,
            # this is our least awful option

            label = app.__name__.rsplit('.', 1)[0]
            while label:
                try:
                    get_app(label)
                except ImproperlyConfigured:
                    label = label.split('.', 1)[-1]
                else:
                    break

            call_command('reset', label, verbosity=0, interactive=False, database='default')

        # reset configuration
        from django import conf
        reload(conf)
