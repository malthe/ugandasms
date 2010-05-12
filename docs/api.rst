API Reference
==============

This is a reference on public classes and functions in the system.

Routing system
--------------

.. automodule:: router.parser

  .. autoclass:: Parser

  .. autoclass:: ParseError

.. automodule:: router.models

  .. autoclass:: Message
     :members:   uri, text, time, user, anonymous, transport, ident

  .. autoclass:: Incoming
     :members:   handle, reply

  .. autoclass:: Outgoing
     :members:   delivered

  .. autoclass:: User

.. automodule:: router.transports

  .. autoclass:: Transport
     :members:   incoming, send

  .. autoclass:: Kannel
     :members:   fetch, handle

