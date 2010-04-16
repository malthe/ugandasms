Overview
========

SMS-CVS is an SMS reporting system designed for a pilot
deployment "Community Vulnerability Surveillance" by UNICEF in the
Acholi region of Uganda.

Platform
--------

- Python 2.6 (with SQLAlchemy 0.6)
- Kannel 1.4.3

Development
-----------

Running all tests::

  $ easy_install-2.6 nose
  $ python2.6 setup.py nosetests

Building documentation::

  $ make html
  $ make latex
  $ cd _build/latex
  $ make all-pdf

License
-------

This software is made available as-is under the BSD license.
