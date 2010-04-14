Protocol
========

This document details the message protocol.

.. warning:: This is a draft specification, subject to change.

Message format
--------------

Any message will consist of one or more sections in which a message
token (single word prefixed by the ``+`` character, e.g. ``+JOIN``)
precedes a set of parameters for that section. An example:

::

  +EPI 12 4 81 +BD 1 0

.. -> input

   >>> parse(input)

This message--an aggregated incident report--includes two (required)
message tokens to help structure input.

Subscription
------------

The subscription subsystem handles user registration.

Registration
~~~~~~~~~~~~

New users of the system are required to register using the
``+REGISTER`` command. Users must provide a name and optionally
location:

.. note:: To harmonize locations, a geocoding system might be employed in the future.

The idea with a separate registration step is that users might
subscribe to zero or more services; keeping user registration separate
allows us to keep service subscription simple.

::

  +REGISTER <name>[, <location>]

Example:

::

  +REGISTER Jonathan Olel, Awach, Gulu

.. -> input

  >>> jonathan.send(input)

If this is the first time the user registers with the system, the
following reply is sent as feedback:

::

  Welcome, Jonathan Olel (#0001). You have been registered.

.. -> output

  >>> assert_equals(jonathan.receive(), output)

Repeat registrations are interpreted as updates:

::

  +REGISTER Jonathan Olel, Patiko, Gulu

.. -> input

  >>> jonathan.send(input)

The system replies to inform the user that the update was succesful.

::

  Hello, Jonathan Olel (#0001). You have updated your information.

.. -> output

  >>> assert_equals(jonathan.receive(), output)

Community Vulnerability Surveillance
------------------------------------

This subsystem implements a set of commands that together form a
framework to perform community vulnerability surveillance in the
field.

Subscription
~~~~~~~~~~~~

Users subscribe to the system using a command that corresponds to
their role in the system:

Village Health Team

  ::

    +VHT 508

  .. -> intput

  Subscription feedback:

  ::

    You have joined the Community Vulnerability Surveillance System as VHT.
    Reports will be sent to Gulu District.
