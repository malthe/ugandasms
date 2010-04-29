import re

from django.db import models
from .orm import Base

def camelcase_to_underscore(str):
    return re.sub(
        '(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '-\\1',
        str).lower().strip('-')

class Message(Base):
    """SMS message.

    The ``text`` attribute contains the original text.
    """

    sender = models.CharField(max_length=12)
    receiver = models.CharField(max_length=12)
    text = models.CharField(max_length=160)
    time = models.DateTimeField(null=True)

    @property
    def kind(self):
        ctype = self.polymorphic_ctype
        if ctype is None:
            cls = type(self)
        else:
            cls = self.polymorphic_ctype.model_class()
            if cls is Message:
                return
        return camelcase_to_underscore(cls.__name__)

    @property
    def title(self):
        return self.text

class Delivery(Base):
    """Message delivery confirmation (DLR)."""

    time = models.DateTimeField(null=True)
    message = models.OneToOneField(Message)
    status = models.IntegerField()

    @property
    def success(self):
        return self.status == 1

class Incoming(Message):
    """An incoming message."""

    reply = models.CharField(max_length=160)

class Outgoing(Message):
    """An outgoing message."""
