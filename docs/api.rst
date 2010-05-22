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

   .. autofunction:: identifier([first, consecutive, must_contain])

   .. autofunction:: name

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
     :members:   handle, parse, reply

     .. attribute:: replies

        Relation to the replies given for this message.

  .. autoclass:: Outgoing
     :members:   delivered, sent

     .. attribute:: delivery

        The date when this message was delivered. This field is
        ``None`` unless a delivery confirmation receipt was provided
        to the transport.

     .. attribute:: in_reply_to

        The message to which this is a reply. May be ``None`` if this
        was an unsolicited message.

  .. autoclass:: Peer

  .. autoclass:: User

     .. attribute:: peers

        Set of peers which authenticate this user object.

Messages
----------

.. autoclass:: router.models.NotUnderstood(text=None)

   .. autofunction:: handle([help])

.. autoclass:: router.models.Failure(text=None)

   .. autofunction:: handle()

.. autoclass:: router.models.Broken(text=None, kind=None)

   .. automethod:: handle

   .. attribute:: kind

      The name of the message class which failed, converted into a
      human-readable string.

Transports
~~~~~~~~~~

.. automodule:: router.transports

  .. autoclass:: Transport

     .. attribute:: name

        Name of the transport.

  .. autoclass:: router.transports.Message
     :members:   incoming

     .. automethod:: parse(text)

GSM
---

.. autoclass:: router.transports.GSM

Kannel
------

.. autoclass:: router.transports.Kannel
   :members:   fetch, handle

.. autofunction:: router.views.kannel

.. _testing:

Testing
~~~~~~~

The platform is fully tested; this includes the applications that come
with the system.

We do not use Django's own test runner. Instead tests should be run
through :mod:`Setuptools` using the ``nose`` extension::

  $ python setup.py nosetests

Note that you must first install the :mod:`nose` package::

  $ easy_install nose

Unit tests
----------

.. autoclass:: router.testing.UnitTestCase()

Functional tests
----------------

.. autoclass:: router.testing.FunctionalTestCase()

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

The functional test case does not require or load your ``settings.py``
file. There is currently no support for integration testing.

Configure it this way::

  gateway = Gateway("gateway")
  bob = Peer(gateway, u"bob")

Bob can now send and receive messages::

  >>> bob.send("+ECHO Hello world+")
  >>> bob.receive()
  'Hello world'

Gateway
-------

To test communication between multiple peers and the system, the
following framework is available.

.. autoclass:: router.testing.Gateway

.. autoclass:: router.testing.Peer

   .. automethod:: send(text)

   .. automethod:: receive()

Coverage
--------

The :mod:`nose` package comes with integration to
:mod:`coverage`. It's a separate package that must first be installed::

  $ easy_install coverage

To receive a test coverage report after running tests, simply amend
``--with-coverage`` to the command line::

  $ python setup.py nosetests --with-coverage

