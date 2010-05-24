Architecture
============

The system is designed around the concept of transports which are
bridges that bring in requests from remote peers and dispatch
responses.

These requests may be text messages, form submissions, USSD sessions
or other types of request/response schemes.

Currently only text messages are catered for.

Messages
--------

The message transport deals with incoming and outgoing text
messages. Communication may happen through a GSM modem or other
gateway.

Incoming messages are sent to a router which is configurable through
the ``MESSAGE_ROUTER`` setting. The router is responsible for breaking
messages up into one or more forms, parsing and handling each one in
turn.

The exact operation of the router is specific to each implementation:

.. autoclass:: router.router.Sequential
   :noindex:

.. _identification:

Identification
~~~~~~~~~~~~~~

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

