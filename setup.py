#!/usr/bin/env python # -- coding: utf-8 --

__version__ = '1.0dev'

import os
import sys

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

ROLES = """\
.. role:: mod(emphasis)
.. role:: term(emphasis)
"""

long_description = "\n\n".join((
    ROLES, README, CHANGES))
long_description = long_description.replace('.. code-block:: python', '::')

version = sys.version_info[:3]

install_requires = [
    'WebOb',
    'Otto',
    'Chameleon',
    'SQLAlchemy',
    'PasteScript',
    'PasteDeploy',
    'iso8601',
    ]

setup(
    name="RapidSMS-CVS",
    version=__version__,
    description="Community Vulnerability Surveillance using SMS.",
    long_description=long_description,
    classifiers=[
       "Development Status :: 3 - Alpha",
       "Intended Audience :: Developers",
       "Programming Language :: Python",
      ],
    keywords="rapidsms unicef cvs",
    author="Malthe Borch and UNICEF Uganda T4D Unit",
    author_email="mborch@gmail.com",
    install_requires=install_requires,
    license='BSD',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data=True,
    zip_safe=False,
    tests_require = install_requires + ['manuel', 'nose'],
    entry_points="""
    [paste.app_factory]
    router = protocol.run:make_router

    [paste.server_runner]
    wsgiref = router.testing:server_runner

    [console_scripts]
    install_demo_fixture = protocol.fixtures:install_demo
    """,
    )

