Getting started
===============

In this section you'll learn how to get started with your own project.

Installation
------------

First we need to get the software up and running. In the following we
assume either a system running Linux or Mac OS X.

Make sure you have the right Python interpreter:

.. code-block:: bash

  bash-3.2 $ python
  Python 2.6.1 (r261:67515, Feb 11 2010, 00:51:29)
  [GCC 4.2.1 (Apple Inc. build 5646)] on darwin
  Type "help", "copyright", "credits" or "license" for more information.
  >>>

Check out the software from the repository:

.. code-block:: bash

  bash-3.2 $ git clone http://github.com/malthe/ugandasms.git

Install Django inside a virtual environment:

.. code-block:: bash

  bash-3.2 $ sudo easy_install virtualenv
  bash-3.2 $ virtualenv env
  bash-3.2 $ source env/bin/activate
  bash-3.2 $ easy_install Django==1.2

.. note:: The system is compatible with Django 1.2 as of this time of writing.

Run the tests to see if everything works:

.. code-block:: bash

  bash-3.2 $ python setup.py nosetests

You should see the word ``"OK"`` at the end of the command output. If
you see ``"FAILED"`` then something isn't working as it should.

Setting up a new project
------------------------

If you're new to Django, visit the `tutorial
<http://docs.djangoproject.com/en/dev/intro/tutorial01/>`_ to learn
how to create a Django project.

The checkout includes a sample configuration file. Copy it over so you
can adapt it to your project:

.. code-block:: bash

  bash-3.2 $ cp settings.py.sample settings.py

UgandaSMS works like any other Django application. It comes with a set
of applications that you can add to your ``INSTALLED_APPS``::

  INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'router',                      # <= always add this
  )

To start sending and receiving messages you'll also need at least one
message transport (although the system will start even if you do not
configure one). If you have a USB dongle ready, the sample
configuration might work out of the box. Add the following to your
``settings.py`` file::

  TRANSPORTS = {
      'gsm': {
          'TRANSPORT': 'router.transports.GSM',
          'DEVICE': '/dev/ttyUSB0',
          }
      }

.. note:: On Mac OS X, the popular Huawei devices usually register themselves as ``"/dev/tty.HUAWEIMobile-Modem"``.

If you've been following along, you should be able to start the system
at this point (don't forget to first set up your database tables using
Django's ``syncdb`` command):

.. code-block:: bash

  bash-3.2 $ paster serve development.ini

You should see an output such as the following:

.. code-block:: bash

  2010-05-20 04:38:02,952 - gsm - INFO - Connected to /dev/tty.HUAWEIMobile-Modem...
  Starting server in PID 81842.
  serving on 0.0.0.0:8080 view at http://127.0.0.1:8080

If you see any other messages being logged, this means there's a
problem talking to your modem.

Adding messages
---------------

You enable messages by including them in the ``MESSAGES``
setting. This should be a tuple of strings pointing to message
models.

The :mod:`router.tests` module comes with a set of messages for
testing and demonstration purposes::

  INSTALLED_APPS += (
    'router.tests',
  )

  MESSAGES = (
      "Empty",
      "Echo",
      )

.. -> input

  >>> from router.testing import SETTINGS
  >>> from textwrap import dedent
  >>> exec dedent(input) in SETTINGS.__dict__

Let's try it out! In the following ``>>>`` indicates a message sent to
the system and ``<<<`` indicates a response. You should be able to
repeat the exercise using an actual mobile phone, messaging your
modem.

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

Writing your own messages
-------------------------

You will almost always want to either write your messages from scratch
or customize one or more of the messages that come with the system.

Message models all inherit from :class:`router.models.Incoming`. The
following methods are required:

.. method:: parse()

   Parses text input using :mod:`picoparse` functions. See
   :data:`router.models.Incoming.parse`.

.. method:: handle(**result)

   Message handler. This method will be passed the parser result. See
   :data:`router.models.Incoming.handle`.

For a reference on the :mod:`picoparse` library, see its `readme
<http://github.com/brehaut/picoparse/blob/master/README.markdown>`_
document. Here's a basic example of a ``parse`` function::

  from picoparse import remaining
  from picoparse.text import caseless_string
  from picoparse.text import whitespace1

  from router.parser import FormatError

  def parse_hello_message():
      caseless_string("+hello")
      try:
          whitespace1()
          name = "".join(remaining())
      except:
          raise FormatError(u"Input error. Format: +HELLO <name>.")

      return {
          'name': name
          }

Any remaining text after the parse function completes will be subject
to another parse loop. This means that a single text message may parse
into multiple incoming message objects, each of which are handled
independently, as if they arrived separately. For this reason it is
recommended to use a distinguishable prefix such as ``"+"`` in front
of any one message e.g. ``"+HELLO ..."``.

To guard against remaining text being subject to an additional loop, a
parser may use the following pattern::

  if picoparse.peek():
      raise FormatError(
          "Unexpected text: %s." %
          "".join(picoparse.remaining()))

Note that whitespace is trimmed already before text enters the parser,
so if ``peek()`` returns any non-trivial value, it means there's
indeed remaining text which would subject to another parse. The text
may contain other characters that you'll want to ignore, however. For
instance, you could strip off any punctuation characters appearing at
the end using e.g.::

  many(partial(one_of, ',.'))

If an additional parse loop is required, and fails, the user is still
notified of this, since the remaining text will parse into a
``NotUnderstood`` message.

To use a parser function defined at module level for a message model,
wrap it using the ``staticmethod`` decorator. The return value of the
parser function will be passed into the message handler as keyword
arguments::

  class Hello(Incoming):
      parse = staticmethod(parse_hello_message)

      def handler(self, name=None):
          self.reply("Hello, %s!" % name)

Trying it out
-------------

To use the message we first have to enable it::

  MESSAGES += (
      "Hello",
      )

There are two different approaches to take in terms of testing how
messages work; both have its own merit:

1) Trial and error -- *easy to get started with*
2) Scripted testing -- *more work up front, less work down the road*

The messages that are included with the system are all tested using
automated scripting.

For the first method you can make use of the two included command-line
extensions ``parse`` and ``handle``, corresponding to the required
methods on the message models:

.. code-block:: bash

  bash-3.2 $ python manage.py parse "+ECHO Hello world!"
  Echo: {'echo': u'hello'}

  bash-3.2 $ python manage.py handle "+ECHO Hello world!"
  1/1 2010-05-20T06:40:18.856503
  --> +echo hello
  ---------------
      1/1 script://mborch
      <-- hello

While the ``parse`` command simply shows how the system interprets the
text messages and translates it into one or more messages, the
``handle`` command actually processes it, possibly writing changes to
the database.

To work instead with a scripted test case (recommended), create a file
``tests.py`` and write a unit test for your parser (see
:class:`router.testing.UnitTestCase`) and a functional test for your
handler (see :class:`router.testing.FunctionalTestCase`),
respectively. The following is a sample test module for the *echo*
message::

  from router.testing import FunctionalTestCase
  from router.testing import UnitTestCase

  class ParserTest(UnitTestCase):
      @staticmethod
      def parse(text):
          from ..models.tests import Echo
          from picoparse import run_parser
          return run_parser(Echo.parse, text)[0]

      def test_echo(self):
          data = self.parse("+ECHO Hello world!")
          self.assertEqual(data, {'echo': 'Hello world!'})

  class HandlerTest(FunctionalTestCase):
      INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
          'router.tests',
          )

      def test_hello_world(self):
          from router.tests import Echo
          message = Echo()
          message.save()
          message.handle(echo='Hello world!')
          self.assertEqual(message.replies.get().text, 'Hello world!')

Note that if your message handler relies on peer and/or user objects
(see the section on :ref:`identification`), you'll need some additional
steps::

  def test_which_requires_user_object(self):
      from router.models import User
      user = User()
      user.save()

      from router.models import Peer
      message.peer, created = Peer.objects.get_or_create(uri="test://test")
      message.peer.user = user
      message.peer.save()

.. warning:: You should never import anything except test cases at module level. Put imports immediately before the symbols are used (inside the test methods).

Run the tests:

.. code-block:: bash

  bash-3.2 $ python setup.py nosetests
