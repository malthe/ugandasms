import re

from django.db import models
from polymorphic import PolymorphicModel as Model

def camelcase_to_underscore(str):
    return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', str).lower().strip('_')

class ReporterRole(models.Model):
    """Represents the role of the user.  This may put reporters into
    different roles such as community health workers, supervisors and
    hospital staff."""

    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, primary_key=True)

class Reporter(models.Model):
    """An authenticated user.

    The device used to send and receive messages typically provide a
    means of authentication. Since users may use different devices, we
    record a set of :class:`Connection` objects that each
    authenticate a reporter.
    """

    name = models.CharField(max_length=50)
    roles = models.ManyToManyField(ReporterRole)
    connections = ()

    @classmethod
    def from_uri(cls, uri, **kwargs):
        reporter = cls(**kwargs)
        reporter.save()
        connection, created = Connection.objects.get_or_create(uri=uri)
        reporter.connections.add(connection)
        return reporter

    def __unicode__(self):
        return self.name

class CustomForeignKey(models.ForeignKey):
    def __init__(self, *args, **kwargs):
        self.column = kwargs.pop('column')
        kwargs.setdefault('db_column', self.column)
        super(CustomForeignKey, self).__init__(*args, **kwargs)

    def get_attname(self):
        return self.column

class Connection(models.Model):
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
    reporter = models.ForeignKey(Reporter, related_name="connections", null=True)

    def __unicode__(self):
        return self.ident

    @property
    def transport(self):
        """Return transport name."""

        return self.uri.split('://', 1)[0]

    @property
    def ident(self):
        """Return ident string."""

        return self.uri.split('://', 1)[1]

class Message(models.Model):
    """SMS message between a user and the system."""

    uri = None
    text = models.CharField(max_length=160*3)
    time = models.DateTimeField(null=True)
    connection = CustomForeignKey(
        Connection, column="uri", related_name="messages", null=True)

    class Meta:
        ordering = ['-time']

    @classmethod
    def from_uri(cls, uri, **kwargs):
        message = cls(**kwargs)
        connection, created = Connection.objects.get_or_create(uri=uri)
        message.connection = connection
        message.save()
        return message

class Incoming(Message):
    """An incoming message."""

    forms = ()

class Form(Model):
    """Text form appearing in a message."""

    text = models.CharField(max_length=160)
    message = models.ForeignKey(Incoming, related_name="forms")
    erroneous = models.NullBooleanField(null=True)

    prompt = u""

    @property
    def kind(self):
        return camelcase_to_underscore(self.__class__.__name__).replace('_', ' ')

    @property
    def reporter(self):
        """Return :class:`Reporter` object, or ``None`` if not available."""

        return self.message.connection.reporter

    def handle(self, **result):
        """Handle incoming message.

        The keyword arguments in ``result`` are provided by the parser.

        Use :meth:`self.reply` to send one or more replies to this
        form; you may also create other database objects here, or
        update existing ones.

        .. note:: Must be implemented by subclass.
        """

        raise NotImplementedError(
            "Message must implement the ``handle`` function.") # PRAGMA: nocover

    def reply(self, text, reporter=None):
        """Reply to this form.

        This method puts an outgoing message into the delivery queue,
        but does not guarantee immediate delivery.
        """

        assert self.id is not None
        assert self.message.id is not None
        text = self.prompt + text

        if reporter is None:
            uri = self.message.uri
        else:
            uri = reporter.connections.all()[0].uri

        message = Outgoing(text=text, uri=uri, in_reply_to=self)
        message.save()

class Outgoing(Message):
    """An outgoing message."""

    in_reply_to = models.ForeignKey(Form, related_name="replies", null=True)
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

    def is_response(self):
        """Return ``True`` if this outgoing message was a direct
        response to an incoming message (as opposed to an unsolicited
        message or an indirect response to an incoming message)."""

        if self.in_reply_to is not None:
            return self.uri == self.in_reply_to.message.uri
        return False

