Overview
========

SMS-CVS is an SMS reporting system designed for a pilot deployment
"Community Vulnerability Surveillance" in the Acholi region of Uganda.

The software is developed by the UNICEF country office in
Uganda.

Platform
--------

- Python 2.6 (with Django 1.2 r13076)
- Kannel 1.4.3

To install the ``django_polymorphic`` dependency, visit the `homepage
<http://bserve.webhop.org/wiki/django_polymorphic>`_ or download from
the `Github repository
<http://github.com/bconstantin/django_polymorphic>`_.

Setup
-----

To enable the Django admin user interface, copy the contents of your
``django/contrib/admin/media`` directory into a local directory
``./media``.

Development
-----------

Running all tests::

  $ easy_install nose
  $ python setup.py nosetests

To run the server, install (or develop) the package and use
``paster``::

  $ python setup.py develop
  $ easy_install pastescript
  $ paster serve development.ini

Deployment
----------

The ``deployment.ini.sample`` file contains a deployment configuration
template. To customize::

  $ cp deployment.ini.sample deployment.ini

By default it runs an ``scgi`` server on port ``8080``. Here's an
example of a configuration for the `lighttpd
<http://www.lighttpd.net/>`_ software::

  $HTTP["host"] =~ "^host.org$" {
        scgi.server = (
              "" =>
                ( "host" =>
                  (
                    "host" => "127.0.0.1",
                    "port" => 8080,
                    "check-local" => "disable"
                  )
                )
            )
  }

To run the server, simply use ``paster``::

  $ paster serve deployment.ini

Documentation
-------------

The system comes with documentation. To build the outputs (HTML and
PDF formats)::

  $ make html
  $ make latex
  $ cd docs/latex
  $ make all-pdf

Kannel
------

The system requires an ``sms-service``, and optionally the
``sendsms-user`` service.

Here's an example of a ``sms-service`` configuration section::

  group = sms-service
  keyword-regex = .*
  catch-all = yes
  max-messages = 3
  get-url = "http://localhost:8080/kannel?sender=%p&receiver=%P&text=%b&timestamp=%T"
  concatenation = true
  assume-plain-text = true
  accept-x-kannel-headers = true
  omit-empty = true

For an explanation of the various options, refer to the `user guide
<www.kannel.org/download/1.4.3/userguide-1.4.3/userguide.html>`_.

License
-------

This software is made available as-is under the BSD license.
