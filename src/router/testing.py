from unittest import TestCase
from wsgiref.simple_server import make_server

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
    def setUp(test):
        from sqlalchemy import create_engine
        sqlite_memory_db = create_engine('sqlite://')
        from .orm import Session
        session = Session()
        session.configure(bind=sqlite_memory_db)
        from .orm import Base
        Base.metadata.bind = sqlite_memory_db
        Base.metadata.create_all()

    def tearDown(test):
        from .orm import Session
        session = Session()
        session.close()
        from .orm import Base
        Base.metadata.drop_all(bind=session.bind)
