import sys
import logging
import time

try:
    import sms
except ImportError: # pragma: NOCOVER
    sms = None

from datetime import datetime
from threading import Thread
from urllib import urlencode
from urllib2 import Request
from urllib2 import urlopen
from traceback import format_exc
from warnings import warn
from weakref import ref as weakref

from django.db.models import get_model
from django.db.models import get_models
from django.db.models import signals
from django.utils.functional import memoize
from django.dispatch import Signal
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .parser import Parser
from .parser import ParseError
from .models import Incoming
from .models import Outgoing
from .models import Peer
from .models import Broken
from .models import Failure
from .models import NotUnderstood
from .models import camelcase_to_dash

pre_parse = Signal()
post_parse = Signal(providing_args=["data"])
pre_handle = Signal()
post_handle = Signal()
kannel_event = Signal(providing_args=["request", "response"])

class Transport(object):
    """Transport.

    Shared by all transport implementations.

    :param name: Name

    :param options: Options; keys may be provided in any case. All
    options are set as attributes on the transport object.

    If an implementation needs to operate in a separate thread, this
    should be set up in the class constructor.
    """

    def __init__(self, name, options={}):
        self.name = name

        for key, value in options.items():
            setattr(self, key.lower(), value)

class Message(Transport):
    """Message transport.

    This is the base class for all message-based transports.

    When the transport receives an incoming message it should call the
    :meth:`incoming` method for processing.
    """

    _parser_cache = {}

    @property
    def parse(self):
        """Message parser.

        Attempts to parse an incoming text message using the list of
        messages enabled through the ``MESSAGES`` setting in Django's
        settings module. This should be a list of strings on the
        following format::

          [<app_label>.]<model_name>

        The application label may be omitted if there's no ambiguity.
        """

        paths = getattr(settings, "MESSAGES", ())
        return self._get_parser(paths)

    def _get_parser(paths):
        messages = []
        models = get_models()
        for path in paths:
            if path.count('.') == 0:
                for model in models:
                    if model.__name__ == path:
                        break
                else: # PRAGMA: nocover
                    raise ImproperlyConfigured("Model not found: %s." % path)
            elif path.count('.') == 1:
                model = get_model(*path.split('.'))
            else: # PRAGMA: nocover
                raise ImproperlyConfigured("Specify messages as [<app_label>.]<model_name>.")
            if model is None: # PRAGMA: nocover
                raise ImproperlyConfigured("Can't find model: %s." % path)
            messages.append(model)

        return Parser(messages)
    _get_parser = staticmethod(memoize(_get_parser, _parser_cache, 1))

    def incoming(self, ident, text, time=None):
        """Invoked when a transport receives an incoming text message.

        The method uses its message parser on ``text`` to receive a
        message model, a parser result dictionary and any remaining
        text. If the message parser throws a parse error, the message
        class will be of type
        :class:`models.router.NotUnderstood`. The error message will
        be set in the ``help`` attribute. If there's remaining text,
        the loop is repeated, possibly resulting in several incoming
        messages.

        Note that signals are provided to hook into the flow of
        operations of this method:: :data:`pre_parse`, :data:`post_parse`,
        :data:`pre_handle` and :data:`post_handle`.
        """

        time = time or datetime.now()
        messages = []

        while True:
            message = Incoming(text=text, time=time)
            pre_parse.send(sender=message)

            try:
                model, data, text = self.parse(message.text)
            except ImproperlyConfigured, error:
                warn("%s ERROR [%s] - %s.\n\n%s" % (
                    time.isoformat(),
                    type(error).__name__,
                    repr(message.text.encode('utf-8')),
                    format_exc(error)))
                model, data, text = Failure, {}, ""
            except ParseError, error:
                model, data, text = NotUnderstood, {'help': error.text}, ""

            message.__class__ = model
            try:
                message.__init__(text=message.text, time=time)
            except Exception, exc:
                message.__class__ = Broken
                message.__init__(
                    text=unicode(exc),
                    kind=camelcase_to_dash(model.__name__))

            post_parse.send(sender=message, data=data)

            peer, created = Peer.objects.get_or_create(
                uri="%s://%s" % (self.name, ident))
            if created:
                peer.save()
            message.peer = peer
            message.save()
            messages.append(message)

            pre_handle.send(sender=message)
            try:
                message.handle(**data)
            finally:
                post_handle.send(sender=message)

            if not text:
                break

        return messages

class GSM(Message): # pragma: NOCOVER
    """GSM transport.

    :param name: Transport name

    :param options: ``DEVICE`` is the modem serial port (e.g. ``\"COM1\"``) or special device path (e.g. ``\"/dev/ttyUSB0\"``); ``LOG_LEVEL`` sets the logging level (default is ``\"WARN\"`` which is quiet unless there's an error).

    Example::

      TRANSPORTS = {
          'gsm': {
              'TRANSPORT': 'router.transports.GSM',
              'DEVICE': '/dev/ttyUSB0',
          }
      }

    """

    device = None
    log_level = "WARN"

    def __init__(self, *args, **kwargs):
        super(GSM, self).__init__(*args, **kwargs)

        # verify availability of sms module
        if sms is None:
            raise ImportError('sms')

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        level = getattr(logging, self.log_level.upper())
        logger = self.logger = logging.Logger(self.name.upper(), level=level)
        logger.addHandler(handler)

        try:
            self.modem = sms.Modem(self.device)
        except sms.ModemError, error:
            logger.error(error)
        else:
            self.logger.info("Connected to %s..." % self.device)

            # query manufacturer for diagnostics
            self.modem.conn.write("AT+GMI\r")
            self.modem.conn.flush()
            result = self.modem.conn.readall()
            manufacturer = result.split('AT+GMI')[-1].split('OK')[0].strip()
            logger.info("%s identified." % manufacturer.capitalize())

            # query mode availability
            self.modem.conn.write("AT+CMGF=?\r")
            self.modem.conn.flush()
            modeline = self.modem.conn.readall()
            if '1' not in modeline:
                logger.critical("Modem does not support text mode (%s)." % modeline.strip())
                return

            # set text mode
            self.modem.conn.write("AT+CMGF=1\r")
            self.modem.conn.flush()
            result = self.modem.conn.readall()
            if 'OK' not in result:
                logger.critical("Unable to set message mode (%s)." % result.strip())
                return

            # start thread
            thread = Thread(target=self.run)
            thread.start()

    def run(self):
        while True:
            # incoming
            try:
                self.modem.wait(1)
                messages = self.modem.messages()
            except sms.ModemError, error:
                self.logger.warn(error)
                time.sleep(1)
                continue

            if len(messages) > 0:
                self.logger.debug("Received %d messages." % len(messages))

            for message in messages:
                ignored = ""
                if len(message.number) < 6:
                    ignored = " [IGNORED]"
                self.logger.debug("%s --> %s%s" % (
                    message.number, repr(message.text.encode('utf-8')), ignored))
                if not ignored:
                    self.incoming(message.number, message.text, message.date)

            # delete all read (and stored sent) messages
            self.modem.conn.write("AT+CMGD=0,2\r\n")
            self.modem.conn.flush()
            if 'OK' not in self.modem.conn.readall():
                self.logger.critical("Error deleting messages.")
                return

            # outgoing
            messages = Outgoing.objects.filter(
                time=None, peer__uri__startswith="%s://" % self.name)
            if len(messages) > 0:
                self.logger.debug("Sending %d messages..." % len(messages))

            for message in messages.all():
                try:
                    self.logger.debug("%s <-- %s" % (
                        message.ident, repr(message.text.encode('utf-8'))))
                    self.modem.send(message.ident, message.text)
                except sms.ModemError, error:
                    self.logger.critical(error)
                    time.sleep(1)
                else:
                    message.time = datetime.now()
                    message.save()

    def ussd(self, request):
        self.logger.info("Requesting %s..." % request)
        self.modem.conn.write("AT+CUSD=1,\"%s\",15\r" % request)
        self.modem.conn.flush()
        self.logger.info(self.modem.conn.readall().strip())

class Kannel(Message):
    """Kannel transport.

    :param name: Transport name
    :param options: Dictionary; define ``'SMS_URL'`` for the URL for the *sendsms* service and ``'DLR_URL'`` to set the delivery confirmation reply

    Example configuration::

      TRANSPORTS = {
          'kannel': {
              'TRANSPORT': 'router.transports.Kannel',
              'SMS_URL': 'http://localhost:13013/cgi-bin/sendsms?username=kannel&password=kannel',
              'DLR_URL': 'http://localhost:8080/kannel',
          }
      }

    """

    sms_url = None
    dlr_url = None

    timeout = 30.0

    def __init__(self, *args, **kwargs):
        super(Kannel, self).__init__(*args, **kwargs)

        reference = weakref(self)

        # set up event handler for incoming messages
        def on_event(sender=None, request=None, response=None, **kwargs):
            transport = reference()
            if transport is None:
                kannel_event.disconnect(on_event, sender)
            else:
                body, status_code = transport.handle(request)
                response.write(body)
                response.status_code = status_code

        kannel_event.connect(on_event, sender=self.name, weak=False)

        # set up event handler for outgoing messages
        def on_event(sender=None, instance=None, created=False, **kwargs):
            transport = reference()
            if transport is None:
                kannel_event.disconnect(on_event, sender)
            else:
                if created is True and instance.transport == transport.name:
                    transport.send(instance)

        signals.post_save.connect(on_event, sender=Outgoing, weak=False)

    def fetch(self, request, **kwargs): # pragma: NOCOVER
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

        try:
            status = int(request.GET.get('status', 0))
            time = datetime.fromtimestamp(
                float(request.GET['timestamp']))

            if status:
                message_id = int(request.GET['id'])
            else:
                sender = request.GET['sender']
                text = request.GET['text']
        except Exception, exc:
            return "There was an error (``%s``) processing the request: %s." % (
                type(exc).__name__, str(exc)), "406 Not Acceptable"

        # the statuses are used by kannel; 1: Delivered to phone, 2:
        # Non-Delivered to Phone, 4: Queued on SMSC, 8: Delivered to
        # SMSC, 16: Non-Delivered to SMSC; since we use the bitmask 3,
        # we can simply check for success or failure
        if status == 1:
            message = Outgoing.objects.get(pk=message_id)
            message.delivery = time
            message.save()
        else:
            try:
                self.incoming(sender, text, time)
            except Exception, exc:
                return "There was an internal error (``%s``) " \
                       "processing the request: %s." % (
                    type(exc).__name__, str(exc)), "500 Internal Server Error"

        return "", "200 OK"

    def send(self, message):
        url = self.sms_url
        if url is None: # PRAGMA: nocover
            raise ValueError("Must set ``SMS_URL`` parameter for transport: %s." % self.name)

        if '?' not in url:
            url += "?"

        query = {
            'to': message.ident,
            'text': message.text,
            }

        if self.dlr_url is not None:
            query.update({
                'dlr-url': '%s?status=%%d&id=%d&timestamp=%%T' % (
                    self.dlr_url, message.id),
                'dlr-mask': '3'
                })

        request = Request(
            url+'&'+urlencode(query)
            )

        response = self.fetch(request, timeout=self.timeout)
        if response.code // 100 == 2:
            message.time = datetime.now()
            message.save()
