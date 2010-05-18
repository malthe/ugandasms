Overview
========

UgandaSMS is an open-source SMS application server licensed under the
BSD license.

The system is written in `Python <http://www.python.org>`_ and uses
the `Django <http://www.djangoproject.com>`_ web framework. It comes
with a :ref:`set of apps <applications>` that can be used as is or be
extended to meet your requirements.

*Community Health*

  This app provides a community vulnerability surveillance system. It
  was designed for use in rural areas of Uganda.

The `Kannel <http://www.kannel.org/>`_ SMS gateway is the default
option for connectivity, but it's easy to write your own message
transport.

Distinct features:

- Modular architecture
- Flexible token-based message parsing
- Support for multiple message payload
- Follows established Django conventions

All parts of the system are documented and tested.

Example
-------

Below is an example of an *echo* application. It will accept an SMS
message that starts with the string ``+ECHO`` (case-insensitive in
this example) and echoes back the remaining string.

Add the following model to your Django ``models.py``::

  from router.models import Incoming
  from picoparse import remaining
  from picoparse.text import caseless_string
  from picoparse.text import whitespace1

  class Echo(Incoming):
       @staticmethod
       def parse():
           caseless_string("+echo")
           whitespace1()
           return {
               'echo': "".join(remaining())
               }

       def handle(self, echo=None):
           self.reply(u"You wrote: %s." % echo)

To enable this message, add it to the list of messages in your ``settings.py``::

  MESSAGES = (
      "myapp.Echo",
      )

We could now try and send a text message that match the parser we defined above::

  >>> +ECHO Hello world!

When an echo message is received by the system it is automatically
saved in the database as well. To query for the message we sent::

  >>> message = Echo.objects.get()
  >>> print message.text
  u'Hello world!'

Messages are *polymorphic*. We get an echo message even if we query
the ``Incoming`` base class::

  >>> message = Incoming.objects.get()
  >>> isinstance(message, Echo)
  True

An incoming message may see zero or more replies depending on the
handler (or perhaps a reply is only added later on by a cron-job or
other delayed activity). In our case there is just a single reply,
which is the message echoed back::

  >>> message.replies.count()
  1
  >>> reply = message.replies.get()
  >>> print reply.text
  u'Hello world!'

Testing
-------

The system includes an automated test suite. It requires the `nose
<http://somethingaboutorange.com/mrl/projects/nose>`_ testing library.

Running all tests::

  $ easy_install nose
  $ python setup.py nosetests

To use PostgreSQL, set the ``WITH_POSTGRESQL`` environment variable to
any true value.

See the chapter on :ref:`testing` to learn how to write your own tests.

Contribution
------------

If you find this software useful, please feel welcome and encouraged
to contribute with bug fixes, documentation or new features.

The most important requirement for a change to be merged into the
``master`` branch of the repository is that test coverage remains at
full coverage -- 100%. However, we also ask that all new features are
documented.

Repository: `http://github.com/malthe/ugandasms <http://github.com/malthe/ugandasms>`_

Documentation
-------------

To build the documentation outputs (HTML and PDF formats)::

  $ make html
  $ make latex
  $ cd build/latex
  $ make all-pdf

License
-------

This software is made available as-is under the BSD license.

Contents
========

.. toctree::
   :numbered:
   :maxdepth: 2

   getting_started.rst
   architecture.rst
   testing.rst
   wsgi.rst
   api.rst
   apps.rst
   glossary.rst

Indices and tables
==================

* :ref:`search`
* :ref:`glossary`
