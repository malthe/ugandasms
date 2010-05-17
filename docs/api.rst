API Reference
==============

This is a reference on public classes and functions in the system.

Base system
-----------

This section details the API of the base system.

Parser
~~~~~~

.. automodule:: router.parser

  .. autoclass:: Parser

  .. autoclass:: ParseError

Models
~~~~~~

.. automodule:: router.models

  .. autoclass:: Message
     :members:   user, transport, ident

     .. attribute:: text

        The message body string.

     .. attribute:: time

        The time a message was received.

  .. autoclass:: Incoming
     :members:   handle, reply

  .. autoclass:: Outgoing
     :members:   delivered

  .. autoclass:: User

     .. attribute:: peers

        Set of peers which authenticate this user object.

Transports
~~~~~~~~~~

.. automodule:: router.transports

  .. autoclass:: Transport
     :members:   incoming, send

  .. autoclass:: Kannel
     :members:   fetch, handle

.. automodule:: router.views

   .. autofunction:: kannel

Testing
~~~~~~~

.. automodule:: router.testing

  .. autoclass:: UnitTestCase()

  .. autoclass:: FunctionalTestCase()

     .. attribute:: INSTALLED_APPS

        Add any Django apps that are required for the test here, e.g.::

          INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
              'myapp',
              )

     .. attribute:: BASE_SETTINGS

        This setting contains convenient default settings for a
        functional test. You will normally not need or want to change
        this setting.

     .. attribute:: USER_SETTINGS

        These settings will be available in the Django settings module
        during testing.

        This is typically used to define which messages should be
        available, or to set up transports.
