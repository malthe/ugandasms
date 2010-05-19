API Reference
==============

This is a reference on public classes and functions in the system.

This section details the API of the base system.

Parser
~~~~~~

The parser module provides the ``Parser`` class which wraps a list of
models and provides a function that matches a text against them:

.. autoclass:: router.parser.Parser

Helper functions
----------------

The :mod:`router.parser:` module also contains a number of utility
parser functions that you are encouraged to make use of:

.. automodule:: router.parser

   .. function:: comma()

      Parses a comma.

   .. autofunction:: date

   .. function:: dot()

      Parses a period (dot).

   .. function:: digit()

      Parses a single digit.

   .. function:: digits()

      Parses one or more digits.

   .. autofunction:: floating

   .. autofunction:: next_parameter

   .. autofunction:: one_of_strings

   .. autofunction:: separator(parser=comma)

   .. autofunction:: tags

   .. autofunction:: timedelta

Exceptions
----------

.. autoclass:: router.parser.ParseError

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

Kannel
------

.. autoclass:: router.transports.Kannel
   :members:   fetch, handle

.. autofunction:: router.views.kannel

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
