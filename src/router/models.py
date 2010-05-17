import re

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from polymorphic import PolymorphicModel as Model
from picoparse import any_token
from picoparse import fail
from picoparse import optional
from picoparse import remaining
from picoparse.text import whitespace

def camelcase_to_dash(str):
    return re.sub(
        '(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '-\\1',
        str).lower().strip('-')

class User(Model):
    """Authenticated user.

    The device used to send and receive messages typically provide a
    means of authentication. Since users may use different devices, we
    record a set of *peers* that authenticate a user.
    """

    peers = ()

class CustomForeignKey(models.ForeignKey):
    def __init__(self, *args, **kwargs):
        self.column = kwargs.pop('column')
        kwargs.setdefault('db_column', "%s_id" % self.column)
        super(CustomForeignKey, self).__init__(*args, **kwargs)

    def get_attname(self):
        return self.column

class Peer(Model):
    """Device identification object.

    The ``uri`` attribute identifies the remote device in terms of a
    transport token and an identification string.

    Examples:

      kannel://256703945965
      twitter://bob
      email://bob@host.com


    The transport token identifies a transport; this is configured in
    the Django settings module under the ``TRANSPORTS`` key.
    """

    uri = models.CharField(max_length=30, primary_key=True)
    user = models.ForeignKey(User, related_name="peers", null=True)

class Message(Model):
    """SMS message between a user and the system.

    The ``user`` attribute holds a relation to the user. If the user
    is not registered, the object may not exist.
    """

    uri = None
    text = models.CharField(max_length=160*3)
    time = models.DateTimeField(null=True)
    peer = CustomForeignKey(Peer, column="uri", related_name="messages", null=True)

    def get_user(self):
        """Return user object, or ``None`` if not available."""

        try:
            return self.peer.user
        except ObjectDoesNotExist:
            pass

    def set_user(self, user):
        self.peer.user = user

    user = property(get_user, set_user)

    @property
    def transport(self):
        """Return transport name."""

        return self.uri.split('://', 1)[0]

    @property
    def ident(self):
        """Return ident string."""

        return self.uri.split('://', 1)[1]

    class Meta:
        ordering = ['-time']

class Incoming(Message):
    """An incoming message."""

    parse = None
    replies = ()

    def handle(self):
        """Handle incoming message.

        The return value is used as the message reply; a ``None``
        value indicates no reply.
        """

        raise NotImplementedError(
            "Message must implement the ``handle`` function.") # PRAGMA: nocover

    def reply(self, text):
        """Schedule an outgoing message as reply to this message."""

        assert self.id is not None
        message = Outgoing(text=text, uri=self.uri, in_reply_to=self)
        message.save()

class Outgoing(Message):
    """An outgoing message."""

    in_reply_to = models.ForeignKey(Incoming, related_name="replies", null=True)
    delivery = models.DateTimeField(null=True)

    @property
    def delivered(self):
        """Return ``True`` if message was confirmed delivered."""

        return self.delivery is not None

class Echo(Incoming):
    """An echo message."""

    @staticmethod
    def parse():
        remaining()

    def handle(self):
        self.reply(self.text)

class Empty(Incoming):
    """The empty message."""

    @staticmethod
    def parse():
        """Fail if any token is parsed.

        >>> from picoparse import run_parser

        The empty message parses (whitespace is ignored).

        >>> run_parser(Empty.parse, ' ') is not None
        True

        Any non-trivial input fails.

        >>> run_parser(Empty.parse, 'hello') # doctest: +ELLIPSIS
        Traceback (most recent call last):
         ...
        NoMatch: ...
        """

        whitespace()
        if optional(any_token, None):
            fail()

    def handle(self):
        self.reply(u"You sent a message with no text.") # pragma: NOCOVER

class NotUnderstood(Incoming):
    """Any message which was not understood."""

    def handle(self, help=None):
        self.reply('Message not understood: %s.' % help)

class Broken(Incoming):
    """Broken message."""

    kind = models.CharField(max_length=30)

    def handle(self):
        self.reply("System error handling message: %s (type: %s)." % (
            self.text, self.kind.replace('-', ' ')))

