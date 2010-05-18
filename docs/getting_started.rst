Getting started
===============

The system works just like Django does. As a minimum, you'll want to
add ``'router'`` to the list of ``INSTALLED_APPS``::

  INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'router',
  )

To start sending and receiving messages you'll also need at least one
message transport::

  TRANSPORTS = {
      'kannel': {
          'TRANSPORT': 'router.transports.Kannel',
          'SMS_URL': 'http://localhost:13013/cgi-bin/sendsms?username=kannel&password=kannel',
          'DLR_URL': 'http://localhost:8080/kannel',
          }
      }

Setting up Kannel
-----------------

The `Kannel <http://www.kannel.org>`_ software comes with most Linux
distributions including Debian and Ubuntu.

Configuration for simple cases is straight-forward.

All settings go into a ``kannel.conf`` file. The format requires you
to first name what group you're configuring followed by a set of
options. Consult the `user guide
<www.kannel.org/download/1.4.3/userguide-1.4.3/userguide.html>`_ for
an explanation of the different groups.

The following is a sample ``core`` configuration::

  group = core
  admin-port = 13000
  smsbox-port = 13001
  admin-password = admin
  admin-deny-ip = "*.*.*.*"
  box-allow-ip = "127.0.0.1""
  wdp-interface-name = "*"
  log-file = "/var/log/kannel/bearerbox.log"
  box-deny-ip = "*.*.*.*"

To listen for incoming messages, you need to start an ``sms-service``.

Here's an example of a ``sms-service`` configuration section. You'll
notice that it expects the Django application to run on ``localhost``
port ``8080`` with the Kannel view URL-mapped at ``/kannel``::

  group = sms-service
  keyword-regex = .*
  catch-all = yes
  max-messages = 3
  get-url = "http://localhost:8080/kannel?sender=%p&receiver=%P&text=%b&timestamp=%T"
  concatenation = true
  assume-plain-text = true
  accept-x-kannel-headers = true
  omit-empty = true

To configure outgoing messages you must configure the ``smsbox`` group
and an ``sendsms-user`` service::

  group = smsbox
  bearerbox-host = localhost
  sendsms-port = 13013
  log-file = "/var/log/kannel/smsbox.log"
  log-level = 0

  group = sendsms-user
  username = kannel
  password = kannel
  concatenation = true
  max-messages = 3
  user-deny-ip = "*.*.*.*"
  user-allow-ip = "127.0.0.1"

Adding messages
---------------

The system will attempt to handle incoming messages by going through
the list in the ``MESSAGES`` Django setting and attempt to parse the
text.

To try it out, add the following definition::

  MESSAGES = (
      "Empty",
      "Echo",
      )

.. -> input

  >>> from router.testing import SETTINGS
  >>> from textwrap import dedent
  >>> exec dedent(input) in SETTINGS.__dict__

Both of these messages come included with the *router* app. Any
non-trivial message will be played back to you, and if you send an
empty message, the system will tell you so.

Let's try it out!

In the following ``>>>`` indicates a message sent to the system and
``<<<`` indicates a response.

  >>> +ECHO Hello, world!

.. -> input

We get the message played back to us::

  <<< Hello, world!

.. -> output

  >>> bob.send(input)
  >>> assert_equals(bob.receive(), output)

Or, if we send an empty message::

  >>>

.. -> input

This will prompt a helpful response that the message was empty::

  <<< You sent a message with no text.

.. -> output

  >>> bob.send(input)
  >>> assert_equals(bob.receive(), output)
