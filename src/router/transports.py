from datetime import datetime
from functools import partial
from urllib import urlencode
from urllib2 import Request
from urllib2 import urlopen

from django.core.exceptions import ObjectDoesNotExist
from django.utils.importlib import import_module
from django.db.models import get_models
from django.db.models import signals
from django.conf import settings

from .parser import Parser
from .models import Outgoing
from .models import Peer

@partial(signals.post_save.connect, sender=Outgoing, weak=False)
def outgoing(sender, instance=None, created=None, **kwargs):
    """Send outgoing message on first save."""

    if created is True:
        transport = get_transport(instance.transport)
        transport.send(instance)

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
        self.parse = Parser(get_models())

        for key, value in options.items():
            setattr(self, key.lower(), value)

    def incoming(self, ident, text, time):
        message = self.parse(text)
        message.time = time
        message.uri = uri="%s://%s" % (self.name, ident)
        message.save()

        # ensure that we have a peer record for this sender
        try:
            Peer.objects.get(uri=message.uri)
        except ObjectDoesNotExist:
            peer = Peer(uri=message.uri)
            peer.save()

        message.handle()

    def outgoing(self, message):
        raise NotImplementedError("Must be implemented by subclass.")

class Kannel(Transport):
    """Kannel transport.

    Configuration options:

      SMS_URL   The URL for the ``sendsms`` service
      DLR_URL   The URL for the delivery confirmation reply

    The ``handle`` method accepts HTTP requests with CGI parameters
    defined as follows:

    Always:

      timestamp  integer epoch value

    Incoming text:

      sender     telephone number
      text       message text

    Delivery confirmation:

      status     positive integer value means this is a delivery confirmation
      id         delivery confirmation id

    """

    sms_url = None
    dlr_url = None

    timeout = 30.0

    def fetch(self, request, **kwargs):
        return urlopen(request, **kwargs)

    def handle(self, request):
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
                'from': message.ident,
                'text': message.text
                }),
            headers={
                'X-Kannel-DLR-Url': '%s?status=%%d&id=%d&timestamp=%%T' % (
                self.dlr_url, message.id),
                'X-Kannel-DLR-Mask': '3'})

        response = self.fetch(request, timeout=self.timeout)
        message.time = datetime.now()
