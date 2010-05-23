.. _transports:

Transports
==========

This section provides detailed information about the included
transports.

GSM
---

Using a locally attached GSM modem (or connected via bluetooth) is an
easy way to get started.

.. class:: GSM(name[, options])

See :class:`router.transports.GSM` for detailed information.

Kannel
------

The `Kannel <http://www.kannel.org>`_ application comes with most
Linux distributions including Debian and Ubuntu. It's an SMS gateway
software that supports a wide range of scenarios and hardware
configurations.

.. class:: Kannel(name[, options])

See :class:`router.transports.Kannel` for detailed information.

Configuration
~~~~~~~~~~~~~

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

Integration
~~~~~~~~~~~

The Kannel transport needs exposure as a regular Django view for
incoming messages. Use the :func:`kannel` view callable by adding an
entry into your URL mapping table::

  from router.views import kannel

  urlpatterns = patterns(''
    (r'^kannel/', kannel),
    )

This view assumes that your Kannel transport is registered under the
name ``"kannel"``.

Writing your own transport
--------------------------

To write your own transport, you must implement the logic required for
receiving incoming messages from your desired communications channel
and provide a ``send`` method for outgoing communication.

Transports should inherit from the ``Transport`` base class. When an
incoming message is received, call its ``incoming`` method. It takes
two mandatory arguments and otionally, the time of arrival:

.. method:: incoming(ident, text[, time])

An example of a transport which starts a thread and sends a message
every second (to keep the example simple, we silently drop outgoing
messages)::

  from threading import Thread
  from time import sleep

  from router.transports import Transport

  class EverySecond(Transport):
       def __init__(self, name, options):
           Transport.__init__(self, name, options)

           def counter():
               elapsed = 0
               while True:
                   self.incoming("timer", "%d seconds elapsed." % elapsed)
                   sleep(1.0)

           thread = Thread(target=counter)
           thread.daemon = True
           thread.start()

       def send(self, message):
           pass

To enable this transport, add the following to Django's ``settings.py``::

  TRANSPORTS = {
      "every": {
           "TRANSPORT": "myapp.transports.EverySecond",
           }
      }
