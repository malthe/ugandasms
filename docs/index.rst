Overview
========

UgandaSMS is an open-source SMS application server licensed under the
BSD license.

The system is written in `Python <http://www.python.org>`_ and uses
the `Django <http://www.djangoproject.com>`_ web framework. It comes
with a set of Django apps that can be used *as is* or extended:

*Registration*

  Allows mobile users to register their names.

*Community Health*

  This app provides a community vulnerability surveillance system. It
  was designed for use in rural areas of Uganda.

The `Kannel <http://www.kannel.org/>`_ SMS gateway is the default
option for connectivity, but it's easy to write your own message
transport.

Example
-------

Here is an example of an *echo* application. It will accept an SMS
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
               'text': "".join(remaining())
               }

       def handle(self):
           self.reply(u"You wrote: %s." % self.text)

To enable this message, add it to the list of messages in your ``settings.py``::

  MESSAGES = (
      "myapp.Echo",
      )

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
   :maxdepth: 2

   getting_started.rst
   architecture.rst
   testing.rst
   wsgi.rst
   api.rst
   glossary.rst

Indices and tables
==================

* :ref:`search`
* :ref:`glossary`
