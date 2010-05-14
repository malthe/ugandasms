Architecture
============

The routing system consists of *messages* and *transports*.

Messages enter and exit the system through one or more
transports. These are defined in the global Django settings module.

An incoming message is then parsed into exactly one message class
(possibly one of the system messages ``NotUnderstood`` or
``Broken``). The handler for that message is then called, which may
result in zero or more replies.

The signals ``pre_handle`` and ``post_handle`` provide hooks into the
incoming message flow:

.. function:: router.transports.pre_handle

   Called immediately *before* a message is handled (but after it's been saved).

.. function:: router.transports.post_handle

   Called immediately *after* a message was handled (even if an exception was raised).

Messages
--------

Incoming messages all inherit from ``Incoming``. Any message must
implement two methods::

  @staticmethod
  def parse():
      # use picoparse here and return message initialization kwargs
      pass

  def handle(self):
      # use ``self.reply(text)`` here to send one or more replies to
      # this message, and/or create new database objects.
      pass

For a reference on the :mod:`picoparse` library, see its `readme
<http://github.com/brehaut/picoparse/blob/master/README.markdown>`_
document. Here's a basic example of a ``parse`` method::

  from picoparse import remaining
  from picoparse.text import caseless_string
  from picoparse.text import whitespace1

  from router.parser import ParseError

  @staticmethod
  def parse():
      caseless_string("+register")
      try:
          whitespace1()
          name = "".join(remaining())
      except:
          raise ParseError(u"Input error. Format: +REGISTER <name>.")

      return {
          'name': name
          }

Note that the message model must define database fields corresponding
to the returned dictionary; in this case ``name``::

  name = django.db.models.CharField(max_length=30)

Normally, the original message text is preserved in the ``text``
field. However, this can be overridden by returning a value for the
``'text'`` key::

  return {
      'name': name,
      'text': "register => %s" % name
      }

Identification
--------------

Incoming messages are uniquely identified by a URI which is made up
from the transport name and an identification token (ident).

Here's an example of a message arriving on the transport with the name
``'kannel'`` from a mobile subscriber::

  kannel://256703945965

The ``ident`` of this URI is the string ``'256703945965'``.

For each URI in the system, there is a unique ``Peer`` object. It
satisifes the following relationship::

  peer.message in message.peer.messages

If the peer object corresponds to a registered user, then we can also
access the user object::

  peer.user

Note that one user may be associated to multiple peers. The ``peers``
relation names all registered peers for a particular user
object. Messages have a convienient ``user`` attribute which returns
either ``None`` or a user object. An example of how this can be used
in a message handler::

  def handle(self):
      if self.user is None:
          self.reply(u"Must be a registered user.")
      else:
          self.reply(u"Thank you!")

Transports
----------

Messages enter and exit the system through transports. The system
comes with a transport for the `Kannel <http://www.kannel.org>`_
gateway software. Transports are configured in Django's
``settings.py`` module under the ``TRANSPORTS`` attribute.

A typical configuration of the Kannel transport::

  TRANSPORTS = {
      'kannel': {
          'TRANSPORT': 'router.transports.Kannel',
          'SMS_URL': 'http://localhost:13013/cgi-bin/sendsms?username=kannel&password=kannel',
          'DLR_URL': 'http://localhost:8080/kannel',
          }
      }

This example assumes that the Kannel service is running locally on the
same server as your Django site. Note that if you do not have the
*global sender* option set in the Kannel configuration, you must add a
``from`` parameter to the ``SMS_URL`` setting. This should be the
mobile number for the SMS service.

.. note:: Transports are automatically instantiated when the ``router`` application is configured (more precisely, when the ``Incoming`` message class has been initialized). The transport instances are kept throughout the process life.

The Kannel transport relies on a regular Django view for its incoming
messages. This must be configured in your ``urls.py`` file::

  from router.views import kannel

  urlpatterns = patterns(''
    (r'^kannel/', kannel),
    )

However, some transports will want to start a thread and poll incoming
messages from e.g. a locally attached GSM modem.

When a transport sees an incoming message, it invokes the message
parser to determine what kind of message it is::

  message = parse(text)

It then calls the message handler which enqueues zero or more outgoing
message replies::

  message.handle()

To write your own transport, you must implement the logic required for
receiving incoming messages from your desired communications channel
and provide a ``send`` method for outgoing communication.

Transports should inherit from the ``Transport`` base class. When an
incoming message is received, call its ``incoming`` method. It takes
two mandatory arguments and otionally, the time of arrival::

  self.incoming(sender_ident, message_text, time_of_arrival)

An example of a transport which starts a thread and sends a message
every second (to keep the example simple, we silently drop outgoing
messages)::

  from threading import Thread
  from time import sleep

  from router.transports import Transport

  class EverySecond(Transport):
       def __init__(self, name, options):
           Transport.__init__(self, name, options)

           def counter():
               elapsed = 0
               while True:
                   self.incoming("timer", "%d seconds elapsed." % elapsed)
                   sleep(1.0)

           thread = Thread(target=counter)
           thread.daemon = True
           thread.start()

       def send(self, message):
           pass

To enable this transport, add the following to Django's ``settings.py``::

  TRANSPORTS = {
      "every": {
           "TRANSPORT": "myapp.transports.EverySecond",
           }
      }
