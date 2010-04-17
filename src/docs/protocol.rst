Protocol
========

This document details the message protocol.

.. warning:: This is a draft specification, subject to change.

Message format
--------------

Any message will consist of one or more sections in which a message
token (single word prefixed by the ``+`` character, e.g. ``+JOIN``)
precedes a set of parameters for that section. An example (note that
``>>>`` denotes a message being sent to the system):

::

  >>> +EPI 12 4 81 +BD 1 0

.. -> input

   >>> parse(input)

This message--an aggregated incident report--includes two (required)
message tokens to help structure input.

Subscription
------------

The subscription subsystem handles user registration.

Registration
~~~~~~~~~~~~

New users of the system are required to register using the
``+REGISTER`` command. Users must provide a name and optionally
location:

.. note:: To harmonize locations, a geocoding system might be employed in the future.

The idea with a separate registration step is that users might
subscribe to zero or more services; keeping user registration separate
allows us to keep service subscription simple.

  *+REGISTER <name>[, <location>]*

Example:

::

  >>> +REGISTER Jonathan Olel, Awach, Gulu

.. -> input

  >>> jonathan.send(input)

If this is the first time the user registers with the system, the
following reply is sent as feedback:

::

  <<< Welcome, Jonathan Olel (#0001). You have been registered.

.. -> output

  >>> assert_equals(jonathan.receive(), output)

Repeat registrations are interpreted as updates:

::

  >>> +REGISTER Jonathan Olel, Patiko, Gulu

.. -> input

  >>> jonathan.send(input)

The system replies to inform the user that the update was succesful.

::

  <<< Hello, Jonathan Olel (#0001). You have updated your information.

.. -> output

  >>> assert_equals(jonathan.receive(), output)



Community Vulnerability Surveillance
------------------------------------

This subsystem implements a set of commands that together form a
framework to perform community vulnerability surveillance in the
field.

Location Hierarchy
~~~~~~~~~~~~~~~~~~

A location database hierarchy will need to be created for a range of catchment areas. Catchment areas in Uganda are as follows: Community (HCI), Parish (HCII), Sub-county (HCIII), County (HCIV and Hospitals) and District. 

Each level should feed information and data from the catchment areas beneath it. The database will be prepopulated with all the Health Center names, HMIS ID codes and GIS coordinates.  Note for the HCI level, there are not HMIS ID codes. Instead, Communities will be first sorted under the HCII/HCIII codes for the facilities which they report to, and then resorted by village names, using fuzzy name matching grouping.  


Subscription
~~~~~~~~~~~~

Users subscribe to the system using a command that corresponds to
their role in the system. For the CVS system, there are three primary subscriptions: Village Health Team members, Health Surviellance Officers and Registered Nurses at Outpatient Thereputic Feeding Centers. Subscriptions will place the user at the appropriate level in the hierarchy. 

The VHT works at the HCI level, which will be sorted by the HMIS ID codes for HCII/HCIIIs, which is the lowest level that has HMIS ID codes. They will For Health Surviellence

Village Health Team, followed by the Health Facility HMIS ID code. 

  ::

    >>> +VHT 50864

  .. -> input

  Subscription feedback:

  ::

    <<< You have joined the Community Vulnerability Surveillance System as a
    VHT for Pakooge HCIII in Gulu District. Please resend if there is a 
    mistake.

Health Surviellance Focal Point, followed by the HMIS ID code.

  ::
    >>> +HCS 508

.. -> input

  Subscription feedback:

  ::

    <<< You have joined the Community Vulnerability Surveillance System as a
    Health Center Surviellence Officer for [Pakooge HCIII] in [Gulu 
    District]. Please resend if there is a mistake.


Weekly Epi Reports
~~~~~~~~~~~~~~~~~~

The WHO and MoH sponsored Community Based Disease Surveillance (CBDS) system was set up to capture key epidemiological data at the community and health facility level. One VHT in each community has been trained to carry out data collection efforts. These reports should be sent to the nearest participating health center on a weekly basis. 

Taken from the government form (similiar to HMIS 033B form for Health Units), VHTs are to report on the following diseases: Malaria, Meningitis, Measles, Diarrhea Bloody, Cholera, Persistant Cough (TB) > 2 weeks, AFP/Polio, Guinea Worm, Neonatal Tetanus (3-28 days), Others (Avian Flu, Oncho, Yellow Fever)

While there are 9 key indicators on the "Reporting of Suspected Disease Conditions" form, only 3 are regularly reported on (Malaria, Diarrhea Bloody and TB. Furthermore, a many of the other diseases require immediate response, including Cholera, Meningitis, AFP/Polio, and Guinea Worm.   


Per Case Malnutrition Reports and Referral Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

VHTs are requested to identify malnourished children by cases referred. This will allow strengthening of exisiting referral mechanisms that will attempt to address significant gaps in service delivery. As the system now works, when patients are screened for malnutrition (using MUAC and Oedema) and referred, slips are given. These are taken to the OTC clinics and noted.

However, this system is plagued by inefficiencies. Neither VHTs or OTC clinics know when patients are referred and do not show, and VHTs need to follow up consistently with all patients in an attempt to identify no-shows and defaulters. Additionally, none of this service delivery information is fed upstream, with which to identify and support areas with poor referral rates. 


Per Case Birth Reports and Service Delivery Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Per Case Under-5 Child Death Reports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Free Form Alerts
~~~~~~~~~~~~~~~~


District Prompted Queries, Alerts and Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
