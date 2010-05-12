import re

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from polymorphic import PolymorphicModel as Model
from picoparse import eof

def camelcase_to_dash(str):
    return re.sub(
        '(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '-\\1',
        str).lower().strip('-')

class User(Model):
    """Identified user.

    The instrumented ``peers`` list can be used for identification.
    """

    name = models.CharField(max_length=50, null=True)
    location = models.CharField(max_length=50, null=True)
    peers = ()

    def __unicode__(self):
        return self.name

class CustomForeignKey(models.ForeignKey):
    def __init__(self, *args, **kwargs):
        self.column = kwargs.pop('column')
        kwargs.setdefault('db_column', "%s_id" % self.column)
        return super(CustomForeignKey, self).__init__(*args, **kwargs)

    def get_attname(self):
        return self.column

class Peer(Model):
    """Remote peer object.

    The ``uri`` attribute identifies the peer in terms of a transport
    token and an identification string.

    Examples:

      kannel://256703945965
      twitter://bob
      email://bob@host.com


    The transport token identifies a transport; this is configured in
    the Django settings module under the ``TRANSPORTS`` key.
    """

    uri = models.CharField(max_length=30, primary_key=True)
    user = models.ForeignKey(User, related_name="peers", null=True)

    def __repr__(self):
        return '<Peer uri="%s" at 0x%x>' % (self.uri, id(self))

class Message(Model):
    """SMS message between a user and the system.

    The ``user`` attribute holds a relation to the user. If the user
    is not registered, the object may not exist.
    """

    uri = None
    text = models.CharField(max_length=160)
    time = models.DateTimeField(null=True)
    peer = CustomForeignKey(Peer, column="uri", null=True)

    def get_user(self):
        try:
            return self.peer.user
        except ObjectDoesNotExist:
            pass

    def set_user(self, user):
        self.peer.user = user

    user = property(get_user, set_user)

    @property
    def transport(self):
        return self.uri.split('://', 1)[0]

    @property
    def ident(self):
        return self.uri.split('://', 1)[1]

    class Meta:
        ordering = ['-time']

class Incoming(Message):
    """An incoming message."""

    parse = None
    replies = ()

    @property
    def anonymous(self):
        try:
            return self.user is None
        except ObjectDoesNotExist:
            return True

    def handle(self):
        """Handle incoming message.

        The return value is used as the message reply; a ``None``
        value indicates no reply.
        """

        raise NotImplementedError(
            "Message must implement the ``handle`` function.")

    def reply(self, text):
        """Schedule an outgoing message as reply to this message."""

        message = Outgoing(text=text, uri=self.uri, in_reply_to=self)
        message.save()

class Outgoing(Message):
    """An outgoing message."""

    in_reply_to = models.ForeignKey(Incoming, related_name="replies")
    delivery = models.DateTimeField(null=True)

    @property
    def delivered(self):
        return self.delivery is not None

class Empty(Incoming):
    """The empty message."""

    parse = eof

class NotUnderstood(Incoming):
    """Any message which was not understood."""

    def handle(self):
        self.reply("Message not understood: %s." % self.text)

class Broken(Incoming):
    """Broken message."""

    kind = models.CharField(max_length=30)

    def handle(self):
        self.reply("System error handling message: %s (type: %s)." % (
            self.text, self.kind.replace('-', ' ')))

