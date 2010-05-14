.. _testing:

Testing
=======

The platform is fully tested; this includes the applications that come
with the system.

We do not use Django's own test runner. Instead tests should be run
through :mod:`Setuptools` using the ``nose`` extension::

  $ python setup.py nosetests

Note that you must first install the :mod:`nose` package::

  $ easy_install nose

Writing your own tests
----------------------

All tests should inherit their test case from either of the following
two classes:

.. automodule:: router.testing

  .. autoclass:: UnitTestCase

  .. autoclass:: FunctionalTestCase

Note that neither of these use or require an external ``settings.py``
file. There is currently no support for integration testing.

Coverage
--------

The :mod:`nose` package comes with integration to
:mod:`coverage`. It's a separate package that must first be installed::

  $ easy_install coverage

To receive a test coverage report after running tests, simply amend
``--with-coverage`` to the command line::

  $ python setup.py nosetests --with-coverage
