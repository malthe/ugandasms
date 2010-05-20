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

   .. autofunction:: identifier

   .. autofunction:: name

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

Coverage
--------

The :mod:`nose` package comes with integration to
:mod:`coverage`. It's a separate package that must first be installed::

  $ easy_install coverage

To receive a test coverage report after running tests, simply amend
``--with-coverage`` to the command line::

  $ python setup.py nosetests --with-coverage

