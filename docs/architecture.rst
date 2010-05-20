Architecture
============

The routing system consists of *messages* and *transports*. Messages
enter and exit the system through one or more transports after going
through the following loop:

1) Parse message text into message model and handler arguments
2) Invoke message handler
3) If there's remaining text, go to (1)

Meanwhile, the system makes sure that track is kept of incoming and
outgoing messages.

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

Signals
~~~~~~~

The following signals provide hooks into the incoming message flow
(the ``sender`` of each of the signals is a message instance):

.. function:: router.transports.pre_parse(sender=None, **kwargs)

   Called *before* an incoming message is parsed.

   The ``sender`` of this signal is always of the generic incoming
   message type ``Incoming``.

   Changing the value of the ``text`` attribute in this step will
   directly control the parser input before next step.

.. function:: router.transports.post_parse(sender=None, data=None, **kwargs)

   Called *after* an incoming message is parsed. In this step the
   message instance has been initialized with the class that was given
   by the parser.

   This signal sends an additional ``data`` argument which is the
   return value of the parser function, or if no value was returned,
   an empty dictionary.

   The ``data`` dictionary is passed into the message handler as
   keyword arguments after the ``pre_handle`` step.

.. function:: router.transports.pre_handle(sender=None, **kwargs)

   Called immediately *before* a message is handled (but after it's
   been saved).

.. function:: router.transports.post_handle(sender=None, **kwargs)

   Called immediately *after* a message was handled (even if an
   exception was raised).

