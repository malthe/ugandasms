Overview
========

UgandaSMS is an SMS application server. It includes a set of
applications that can be used directly or built upon:

- Registration
- Community Health

The system is written in Python and uses the Django web framework. It
comes with support for the `Kannel <http://www.kannel.org/>`_
SMS gateway.

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
               'text': remaining()
               }

       def handle(self):
           self.reply(u"You wrote: %s." % self.text)

To enable this message, add it to the list of messages in your ``settings.py``::

  MESSAGES = (
      "myapp.Incoming",
      )

Testing
-------

The system includes an automated test suite. It requires the `nose
<http://somethingaboutorange.com/mrl/projects/nose>`_ testing library.

Running all tests::

  $ easy_install nose
  $ python setup.py nosetests

Documentation
-------------

The system comes with documentation. To build the outputs (HTML and
PDF formats)::

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
   wsgi.rst
   api.rst
   glossary.rst

Indices and tables
==================

* :ref:`search`
* :ref:`glossary`
