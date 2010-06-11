import os
import pwd
import sys

from copy import deepcopy
from unittest import TestCase
from traceback import format_exc
from StringIO import StringIO

from django.test import TestCase

class Gateway(object):
    """Message gateway.

    Use this transport to test communication between two peers.
    """

    def __new__(cls, *args, **kwargs):
        from .transports import Message
        cls = type("Gateway", (cls, Message), {})
        return object.__new__(cls)

    def __init__(self, name, **kwargs):
        self._subscribers = {}
        super(Gateway, self).__init__(name, **kwargs)

    def receive(self, sender, text):
        self._subscribers[sender.ident] = sender
        message = self.incoming(sender.ident, text)
        for form in message.forms.all():
            for reply in form.replies.all():
                self.send(reply)

    def send(self, reply):
        receiver = self._subscribers[reply.connection.ident]
        receiver.receive(reply.text)

        # note delivery time
        reply.delivery = reply.in_reply_to.message.time
        reply.save()

class Peer(object):
    """Network peer.

    Each peer is configured for a :class:`gateway` with a unique ``ident``
    string.
    """

    def __init__(self, gateway, ident):
        self.gateway = gateway
        self.ident = ident
        self._received = []

    def send(self, text):
        """Sends text to gateway."""

        text = text.lstrip("> ")
        assert len(text) <= 160
        self.gateway.receive(self, text)

    def receive(self, text=None):
        """Returns a received message by popping it off the incoming
        stack. If no message was received, the empty string is
        returned.
        """

        if text is None:
            return self._received and self._received.pop(0) or u''
        text = "<<< " + text
        self._received.append(text)

class FormTestCase(TestCase):
    """Adds utility methods for testing forms."""

    default_uri = "test://old"

    @classmethod
    def register_default_user(cls):
        from .models import Reporter
        return Reporter.from_uri(cls.default_uri)

    @classmethod
    def handle(cls, model, text="", uri=None, **kwargs):
        """Handles an incoming message.

        :param model: Form to handle
        :param text: Message body (optional)
        :param uri: Connection URI (defaults to the ``default_uri`` class attribute).

        """

        if uri is None:
            uri = cls.default_uri

        from .models import Incoming
        from datetime import datetime
        time = datetime(1999, 12, 31, 0, 0, 0)
        message = Incoming(text=text, time=time, uri=uri)
        from .models import Connection
        message.connection, created = Connection.objects.get_or_create(uri=uri)
        message.connection.save()
        message.save()
        form = model(text=text, message=message)
        form.save()
        form.handle(**kwargs)
        return form
