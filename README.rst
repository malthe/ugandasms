Overview
========

SMS-CVS is an SMS reporting system designed for a pilot deployment
"Community Vulnerability Surveillance" in the Acholi region of Uganda.

The software is developed by the UNICEF country office in
Uganda.

Platform
--------

- Python 2.6 (with SQLAlchemy 0.6)
- Kannel 1.4.3

Development
-----------

Running all tests::

  $ easy_install nose
  $ python setup.py nosetests

To run the server, install the software in development mode and use
``paster``::

  $ python setup.py develop
  $ easy_install pastescript
  $ paster serve development.ini

Building documentation (HTML and PDF formats)::

  $ make html
  $ make latex
  $ cd docs/latex
  $ make all-pdf

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

Kannel
------

The system requires an ``sms-service``, and optionally the
``sendsms-user`` service.

Here's an example of a ``sms-service`` configuration section::

  group = sms-service
  keyword-regex = .*
  catch-all = yes
  max-messages = 3
  post-url = "http://localhost:8080/kannel?sender=%p&receiver=%P&text=%b&timestamp=%T"
  concatenation = true
  assume-plain-text = true
  accept-x-kannel-headers = true
  omit-empty = true

For an explanation of the various options, refer to the `user guide
<www.kannel.org/download/1.4.3/userguide-1.4.3/userguide.html>`_.

License
-------

This software is made available as-is under the BSD license.
