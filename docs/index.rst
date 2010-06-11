Overview
========

UgandaSMS is an open-source SMS application server licensed under the
BSD license.

The system is written in `Python <http://www.python.org>`_ and uses
the `Django <http://www.djangoproject.com>`_ web framework. It comes
with a :ref:`set of apps <applications>` that can be used as is or be
extended to meet your requirements.

Distinct features:

- Modular architecture
- Flexible token-based message parsing
- Support for multiple message payload
- Follows established Django conventions

All parts of the system are documented and tested.

Example
-------

Below is an example of an *echo* form. It will accept an SMS message
that starts with the string ``+ECHO`` (although case-insensitive in
this example) and echoes back the remaining string.

Add the following model to your Django ``models.py``::

  from router.models import Form
  from router.pico import wrap
  from picoparse import remaining
  from picoparse.text import caseless_string
  from picoparse.text import whitespace1

  class Echo(Form):
       @wrap
       def parse(cls):
           caseless_string("+echo")
           whitespace1()
           return {
               'echo': "".join(remaining())
               }

       def handle(self, echo=None):
           self.reply(u"You wrote: %s." % echo)

To enable this message, add it to the list of messages in your
``settings.py`` and configure the sequential router which match forms
in sequence::

  MESSAGE_ROUTER = 'router.router.Sequential'

  FORMS = (
      "Echo",
      )

We could now try and send a text message that matches our form::

  >>> +ECHO Hello world!

The message is parsed into exactly one form::

  >>> message = Incoming.objects.get()
  >>> message.forms.count()
  1

There can be multiple replies for each form, but our handler just
creates one::

  >>> form = message.forms.get()
  >>> form.replies.get().text
  'Hello world!'

Forms are *polymorphic*. We get back an object of type `Echo` even if
we query the base class::

  >>> form = Form.objects.get()
  >>> isinstance(form, Echo)
  True

Testing
-------

The system includes an automated test suite. It requires the `nose
<http://somethingaboutorange.com/mrl/projects/nose>`_ testing library.

Running all tests::

  $ easy_install nose
  $ python manage.py test

See the API documentation on :ref:`testing` for more information.

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
   apps.rst
   architecture.rst
   transports.rst
   wsgi.rst
   api.rst
   faq.rst
   glossary.rst

Indices and tables
==================

* :ref:`search`
* :ref:`glossary`

.. rubric:: Footnotes

.. [#kannel-interface] Using the HTTP interface provided by the ``sms-service`` and ``sendsms-user`` groups.

.. [#gsm] Requires the `sms <http://pypi.python.org/pypi/sms>`_ package by Amos Latteier.

