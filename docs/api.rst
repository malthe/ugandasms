API Reference
==============

This is a reference on public classes and functions in the system.

This section details the API of the base system.

Models
~~~~~~

.. automodule:: router.models

  .. autoclass:: Form
     :members:   user, handle, reply

     .. attribute:: text

        The form input string.

     .. attribute:: message

        The message object that the form originated from.

     .. attribute:: erroneous

        Indicates whether the form was marked as erroneous during
        parsing (if a :class:`router.router.FormatError` exception was
        raised).

     .. attribute:: replies

        Replies given for this form.

  .. autoclass:: Message
     :members:   transport, ident

     .. attribute:: text

        The message body string.

     .. attribute:: time

        The time a message was received.

  .. autoclass:: Incoming

     .. attribute:: forms

        The forms that resulted from this message.

  .. autoclass:: Outgoing
     :members:   delivered, sent

     .. attribute:: delivery

        The date when this message was delivered. This field is
        ``None`` unless a delivery confirmation receipt was provided
        to the transport.

     .. attribute:: in_reply_to

        The message to which this is a reply, or ``None`` if this is
        an unsolicited message.

  .. autoclass:: Peer

     .. attribute:: user

        Relation to a user object, if applicable. Messages always have
        a peer object, but only messages sent from registered users
        have a user object.

  .. autoclass:: User

     .. attribute:: peers

        Set of peers which authenticate this user object.

Router
~~~~~~

.. autoclass:: router.router.FormatError

.. autoclass:: router.router.Sequential
   :members:   forms, route

Pico
~~~~

The :mod:`router.pico` module also contains a number of utility parser
functions that you are encouraged to make use of:

.. automodule:: router.pico

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

Transports
~~~~~~~~~~

.. automodule:: router.transports

   .. autoclass:: Transport(name[, options])
      :members:

   .. autoclass:: router.transports.Message
      :members:   incoming, router

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

Form tests
----------

.. autoclass:: router.testing.FormTestCase()

Gateway
-------

To test communication between multiple peers and the system, the
following framework is available.

.. autoclass:: router.testing.Gateway

.. autoclass:: router.testing.Peer

   .. automethod:: router.testing.Peer.send(text)

   .. automethod:: router.testing.Peer.receive()

Configure it this way::

  gateway = Gateway("gateway")
  bob = Peer(gateway, u"bob")

Bob can now send and receive messages::

  >>> bob.send("+ECHO Hello world+")
  >>> bob.receive()
  'Hello world'

Coverage
--------

The :mod:`nose` package comes with integration to
:mod:`coverage`. It's a separate package that must first be installed::

  $ easy_install coverage

To receive a test coverage report after running tests, simply amend
``--with-coverage`` to the command line::

  $ python setup.py nosetests --with-coverage

