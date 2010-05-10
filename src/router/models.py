import re

from django.db import models
from polymorphic import PolymorphicModel as Model
from django.core.exceptions import ObjectDoesNotExist

def camelcase_to_dash(str):
    return re.sub(
        '(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '-\\1',
        str).lower().strip('-')

class ProxyForeignKey(models.ForeignKey):
    def get_attname(self):
        return self.db_column

class Message(Model):
    """SMS message.

    The ``text`` attribute contains the original text.
    """

    receiver = models.CharField(max_length=12)
    text = models.CharField(max_length=160)
    time = models.DateTimeField(null=True)
    user = ProxyForeignKey(
        "router.User", to_field="number", db_column="sender",
        related_name="messages", null=True)

    class Meta:
        ordering = ['-time']

    @property
    def kind(self):
        ctype = self.polymorphic_ctype
        if ctype is None:
            cls = type(self)
        else:
            cls = self.polymorphic_ctype.model_class()
            if cls is Message:
                return
        return camelcase_to_dash(cls.__name__)

class Delivery(Model):
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

    @property
    def anonymous(self):
        try:
            return self.user is None
        except ObjectDoesNotExist:
            return True

    def __call__(self):
        """Handle incoming message.

        The return value is used as the message reply; a ``None``
        value indicates no reply.
        """

        raise NotImplementedError(
            "Message must provide the call function.")

class Empty(Incoming):
    """The empty message."""

class NotUnderstood(Incoming):
    """Any message which was not understood."""

    def __call__(self):
        return "Message not understood: %s." % self.text

class Broken(Incoming):
    """Broken message."""

    factory = models.CharField(max_length=30)

    def __call__(self):
        return "System error handling message: %s (type: %s)." % (
            self.text, camelcase_to_dash(self.factory).replace('-', ' '))

