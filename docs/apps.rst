.. _applications:

Applications
============

This is a reference on the Django apps that come with the
system. Simply add the apps you want to use to the list of
``INSTALLED_APPS`` in your settings module.

Community Health
----------------

Django app: ``health``

This application provides a complete system for monitoring and
reporting on community health.

Forms
~~~~~

.. automodule:: health.models

  .. autoclass:: Aggregates

  .. autoclass:: BirthForm

  .. autoclass:: Cure

  .. autoclass:: Muac


Reporter
--------

Django app::

  "reporter"

The *reporter* app allows mobile users to register themselves as
reporters using one or more devices/handsets.

Forms
~~~~~

.. automodule:: reporter.models

  .. autoclass:: Registration

