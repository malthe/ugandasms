from unittest import TestCase
from traceback import format_exc

class Gateway(object):
    """Mobile gateway."""

    def __init__(self, parser):
        self.parser = parser
        self._subscribers = {}

    # def forward(self, receiver, text):
    #     assert receiver != self.receiver
    #     assert receiver in self._subscribers
    #     subscriber = self._subscribers[receiver]
    #     subscriber.receive(text)

    def send(self, subscriber, text):
        self._subscribers[subscriber.uri] = subscriber
        message = self.parser(text)

        # record message
        message.uri = subscriber.uri
        message.save()

        # record peer
        from django.core.exceptions import ObjectDoesNotExist
        try:
            peer = message.peer
        except ObjectDoesNotExist:
            peer = None

        if peer is None:
            from router.models import Peer
            Peer(uri=message.uri).save()

        message.handle()

        from router.models import Outgoing
        replies = Outgoing.objects.filter(in_reply_to=message)
        for reply in replies:
            self.deliver(subscriber, reply, message.time)

    def deliver(self, receiver, reply, time):
        receiver.receive(reply.text)

        # note delivery time
        reply.delivery = time
        reply.save()

class Subscriber(object):
    """Mobile subscriber."""

    def __init__(self, gateway, uri=None):
        self.gateway = gateway
        self.uri = uri
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

class UnitTestCase(TestCase):
    class Settings(object):
        pass

    # this is a global!
    SETTINGS = Settings()

    def setUp(self):
        from django.conf import settings
        from django.conf import global_settings

        if not settings.configured:
            settings.configure(self.SETTINGS)
            self.SETTINGS.__dict__.update(global_settings.__dict__)

class FunctionalTestCase(UnitTestCase):
    INSTALLED_APPS = (
        'django.contrib.contenttypes',
        'router',
        )

    USER_SETTINGS = {}

    def setUp(self):
        super(FunctionalTestCase, self).setUp()

        self.SETTINGS.__dict__.update({
            'DATABASES': {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                    }
                },
            'INSTALLED_APPS': self.INSTALLED_APPS,
            'DLR_URL': 'http://host/kannel',
            })
        self.SETTINGS.__dict__.update(self.USER_SETTINGS)

        from django.db.models.loading import cache
        cache.app_store.clear()
        cache.loaded = False
        cache.handled.clear()
        del cache.postponed[:]

        from django.core.management import call_command
        try:
            call_command('syncdb', verbosity=0, interactive=False, database='default')
        except SystemExit, exc:
            self.fail(format_exc(exc))
        super(FunctionalTestCase, self).setUp()

    def tearDown(self):
        super(FunctionalTestCase, self).tearDown()
        from django.core.management import call_command
        from django.db.models.loading import get_apps

        for app in get_apps():
            label = app.__name__.split('.')[-2]
            try:
                call_command('reset', label, verbosity=0, interactive=False, database='default')
            except SystemExit, exc:
                self.fail(format_exc(exc))
