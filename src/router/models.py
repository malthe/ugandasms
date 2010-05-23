from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from polymorphic import PolymorphicModel as Model

class User(Model):
    """An authenticated user.

    The device used to send and receive messages typically provide a
    means of authentication. Since users may use different devices, we
    record a set of :class:`Peer` objects that each
    authenticate a user.
    """

    peers = ()

class CustomForeignKey(models.ForeignKey):
    def __init__(self, *args, **kwargs):
        self.column = kwargs.pop('column')
        kwargs.setdefault('db_column', self.column)
        super(CustomForeignKey, self).__init__(*args, **kwargs)

    def get_attname(self):
        return self.column

class Peer(Model):
    """Mapping between device and user.

    The ``uri`` attribute identifies the device in terms of the
    transport used and the unique identifier within that transport::

      <transport>://<ident>

    Examples::

      gsm://256703945965
      kannel://256703945965
      twitter://bob
      email://bob@host.com


    The transport token identifies a transport; this is configured in
    the Django settings module under the ``TRANSPORTS`` key.
    """

    uri = models.CharField(max_length=30, primary_key=True)
    user = models.ForeignKey(User, related_name="peers", null=True)

class Message(Model):
    """SMS message between a user and the system."""

    uri = None
    text = models.CharField(max_length=160*3)
    time = models.DateTimeField(null=True)
    peer = CustomForeignKey(Peer, column="uri", related_name="messages", null=True)

    @property
    def user(self):
        """Return :class:`User` object, or ``None`` if not available."""

        try:
            return self.peer.user
        except ObjectDoesNotExist:
            pass

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

    replies = ()
    erroneous = models.NullBooleanField(null=True)

    def handle(self, **result):
        """Handle incoming message.

        The keyword arguments in ``result`` are provided by the parser.

        Use :meth:`self.reply` to send one or more replies to this message;
        you may also create other database objects here, or update
        existing ones.

        .. note:: Must be implemented by subclass.
        """

        raise NotImplementedError(
            "Message must implement the ``handle`` function.") # PRAGMA: nocover

    @staticmethod
    def parse():
        """Return either a dictionary or ``None``.

        This method takes no arguments; input is acquired through the
        use of :mod:`picoparse` parser functions.

        .. note:: Must be implemented by subclass.
        """

    def reply(self, text):
        """Reply to this message.

        This method puts an outgoing message into the delivery queue,
        but does not guarantee immediate delivery.
        """

        assert self.id is not None
        message = Outgoing(text=text, uri=self.uri, in_reply_to=self)
        message.save()

class Outgoing(Message):
    """An outgoing message."""

    in_reply_to = models.ForeignKey(Incoming, related_name="replies", null=True)
    delivery_id = models.IntegerField(null=True)
    delivery = models.DateTimeField(null=True)

    @property
    def delivered(self):
        """Return ``True`` if the message was confirmed delivered."""

        return self.delivery is not None

    @property
    def sent(self):
        """Return ``True`` if the message was sent."""

        return self.time is not None

