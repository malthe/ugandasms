.. _applications:

Applications
============

This is a reference on the Django apps that come with the
system. Simply add the apps you want to use to the list of
``INSTALLED_APPS`` in your settings module.

Health
------

The *health* app allows users to report in routine health reports such
as epidemiological indicator values.

Forms
~~~~~

.. automodule:: health.models

  .. autoclass:: Aggregates

  .. autoclass:: Cure

  .. autoclass:: Muac

Reporter
--------

The *reporter* app allows mobile users to register themselves as
reporters using one or more devices/handsets.

Forms
~~~~~

.. automodule:: reporter.models

  .. autoclass:: Registration

