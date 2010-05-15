from datetime import datetime
from functools import partial
from urllib import urlencode
from urllib2 import Request
from urllib2 import urlopen

from django.db.models import get_model
from django.utils.importlib import import_module
from django.db.models import signals
from django.dispatch import Signal
from django.conf import settings

from .parser import Parser
from .models import Incoming
from .models import Outgoing
from .models import Peer
from .models import Broken
from .models import camelcase_to_dash

@partial(signals.post_save.connect, sender=Outgoing, weak=False)
def outgoing(sender, instance=None, created=None, **kwargs):
    """Send outgoing message on first save."""

    if created is True:
        transport = get_transport(instance.transport)
        transport.send(instance)

@partial(signals.post_init.connect, sender=Incoming, weak=False)
def initialize(sender, **kwargs):
    """Initialize transports."""

    for name in getattr(settings, "TRANSPORTS", ()):
        get_transport(name)

pre_parse = Signal()
post_parse = Signal()
pre_handle = Signal()
post_handle = Signal()

def get_transport(name):
    """Look up and return transport given by ``name``.

    Transports must be defined in under the ``TRANSPORTS`` settings
    key. Each entry is an identifier string that points to a
    configuration dictionary.

    The only required parameter for any transport is the ``TRANSPORT``
    key. This must be the dotted path to a factory class.

    The transport will be instantiated on the first lookup. The
    transport name is passed as the first argument while any
    additional keys in the configuration dictionary will be provided
    as the second argument (not as double-star keyword arguments).
    """

    try:
        transports = settings.TRANSPORTS
    except AttributeError:
        raise RuntimeError("No transports defined.")

    if name not in transports:
        raise ValueError("No such transport: %s." % name)

    configuration = transports[name]

    try:
        transport = configuration["TRANSPORT"]
    except KeyError:
        raise ValueError("Must set value for ``TRANSPORT``.")

    if isinstance(transport, basestring):
        module_name, class_name = transport.rsplit('.', 1)
        module = import_module(module_name)
        factory = getattr(module, class_name)
        transport = configuration["TRANSPORT"] = factory(name, configuration)

    return transport

class Transport(object):
    """Transport base class.

    The ``incoming`` method is a convenience method for transport
    implementations to handle an incoming message. Similarly, delivery
    reports are handled by the ``delivery`` method.

    Transports that receive incoming communication will typically want
    to spawn a daemon-thread upon initialization.
    """

    def __init__(self, name, options):
        self.name = name

        messages = []
        for path in getattr(settings, "MESSAGES", ()):
            if path.count('.') != 1:
                raise ValueError("Specify messages as <app_label>.<model_name>.")
            model = get_model(*path.split('.'))
            if model is None:
                raise ValueError("Can't find model: %s." % path)
            messages.append(model)

        self.parse = Parser(messages)
        for key, value in options.items():
            setattr(self, key.lower(), value)

    def incoming(self, ident, text, time=None):
        """Handle incoming message."""

        message = Incoming(text=text, time=time or datetime.now())

        pre_parse.send(sender=message)
        model, kwargs = self.parse(message.text)

        message.__class__ = model
        try:
            message.__init__(**kwargs)
        except Exception, exc:
            message.__class__ = Broken
            message.__init__(
                text=unicode(exc),
                kind=camelcase_to_dash(model.__name__))

        post_parse.send(sender=message)

        peer, created = Peer.objects.get_or_create(
            uri="%s://%s" % (self.name, ident))
        if created:
            peer.save()
        message.peer = peer
        message.save()

        pre_handle.send(sender=message)
        try:
            message.handle()
        finally:
            post_handle.send(sender=message)

    def send(self, message):
        """Send message using transport.

        This method should be overriden by any transport that wants to
        send outgoing messages.

        The implementation in the base class does nothing (although
        outgoing messages are always stored in the database).

        Only outgoing messages that have been sent should have a
        defined ``time`` (this is a record of when a message
        left the system, not when it was merely queued). It's up to
        the ``send`` method to set this value.
        """

class Kannel(Transport):
    """Kannel transport.

    :param name: Transport name
    :param options: Dictionary; define ``'SMS_URL'`` for the URL for the *sendsms* service and ``'DLR_URL'`` to set the delivery confirmation reply
    """

    sms_url = None
    dlr_url = None

    timeout = 30.0

    def fetch(self, request, **kwargs):
        """Fetch HTTP request.

        Used internally by the Kannel transport.

        This method operates synchronously. Note that the method is a
        convenience for writing tests without setting up an HTTP
        server (replace with a mock implementation).
        """

        return urlopen(request, **kwargs)

    def handle(self, request):
        """
        Accepts Django HTTP requests (method ``GET``) with CGI
        parameters defined as follows:

        Requests can be incoming messages or delivery confirmation
        receipts.

        Required:

        :param timestamp: Epoch integer timestamp (any)

        Incoming messages:

        :param sender: Mobile number
        :param text: Message body

        Delivery confirmation (DLR):

        :param status: Positive integer value means this is a delivery confirmation
        :param id: Message id
        """

        status = int(request.GET.get('status', 0))
        time = datetime.fromtimestamp(
            float(request.GET['timestamp']))

        if status:
            message_id = int(request.GET['id'])
        else:
            sender = request.GET['sender']
            text = request.GET['text']

        # the statuses are used by kannel; 1: Delivered to phone, 2:
        # Non-Delivered to Phone, 4: Queued on SMSC, 8: Delivered to
        # SMSC, 16: Non-Delivered to SMSC; since we use the bitmask 3,
        # we can simply check for success or failure
        if status == 1:
            message = Outgoing.objects.get(pk=message_id)
            message.delivery = time
            message.save()
        else:
            self.incoming(sender, text, time)

    def send(self, message):
        url = self.sms_url
        if url is None:
            raise ValueError("Must set ``SMS_URL`` parameter for transport: %s." % self.name)

        if '?' not in url:
            url += "?"

        request = Request(
            url+'&'+urlencode({
                'to': message.ident,
                'text': message.text,
                'dlr-url': '%s?status=%%d&id=%d&timestamp=%%T' % (
                    self.dlr_url, message.id),
                'dlr-mask': '3'})
            )

        response = self.fetch(request, timeout=self.timeout)
        if response.code // 100 == 2:
            message.time = datetime.now()
