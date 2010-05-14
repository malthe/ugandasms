import os
import sys

from copy import deepcopy
from unittest import TestCase
from traceback import format_exc
from StringIO import StringIO

class Gateway(object):
    """Mobile gateway."""

    def __init__(self, parser):
        self.parser = parser
        self._subscribers = {}

    def send(self, subscriber, text):
        self._subscribers[subscriber.uri] = subscriber
        message = self.parser(text)

        from router.models import Peer
        message.peer, created = Peer.objects.get_or_create(uri=subscriber.uri)
        if created:
            message.peer.save()

        message.save()
        message.handle()

        from router.models import Outgoing
        replies = Outgoing.objects.filter(in_reply_to=message)
        for reply in replies:
            self.deliver(subscriber, reply, message.time)

    def deliver(self, receiver, reply, time):
        receiver.receive(reply.text)

        # note delivery time
        reply.delivery = time
        reply.save()

class Subscriber(object):
    """Mobile subscriber."""

    def __init__(self, gateway, uri=None):
        self.gateway = gateway
        self.uri = uri
        self._received = []

    def send(self, text):
        """Sends text to gateway."""

        text = text.lstrip("> ")
        assert len(text) <= 160
        self.gateway.send(self, text)

    def receive(self, text=None):
        if text is None:
            return self._received and self._received.pop(0) or u''
        text = "<<< " + text
        self._received.append(text)

class UnitTestCase(TestCase):
    """Use this test case for tests which do not require a database."""

    class Settings(object):
        pass

    # this is a global!
    SETTINGS = Settings()

    def setUp(self):
        from django.conf import settings
        from django.conf import global_settings

        if not settings.configured:
            settings.configure(self.SETTINGS)
            self.SETTINGS.__dict__.update(global_settings.__dict__)

        super(UnitTestCase, self).setUp()

class FunctionalTestCase(UnitTestCase):
    """Use this test case for tests which require a database.

    The user account that runs the test suite must have the
    ``CREATEDB`` privilege. When creating test databases, the naming
    convention is defined by the ``_pg_database_name`` property. By
    default this uses the test class name in all lower case.

    For GeoDjango support with PostgreSQL, a PostGIS template with the
    name ``'template_postgis'`` must be installed. If you run the
    tests as a non-superuser, the ``datistemplate`` flag must be set.

    Spatialite is also supported.
    """

    INSTALLED_APPS = (
        'django.contrib.contenttypes',
        'router',
        )

    USER_SETTINGS = {}

    def setUp(self):
        super(FunctionalTestCase, self).setUp()

        if self._pg_enabled:
            DATABASE = self._pg_create_database()
        else:
            if 'django.contrib.gis' in self.INSTALLED_APPS:
                engine = 'django.contrib.gis.db.backends.spatialite'
            else:
                engine = 'django.db.backends.sqlite3'

            DATABASE = {
                'ENGINE': engine,
                'NAME': ':memory:',
                }

        self.SETTINGS.__dict__.update({
            'DATABASES': {
                'default': DATABASE,
                },
            'INSTALLED_APPS': self.INSTALLED_APPS,
            'DLR_URL': 'http://host/kannel',
            })

        self.SETTINGS.__dict__.update(deepcopy(self.USER_SETTINGS))

        # reinitialize connections
        from django import db
        db.connections.__init__(self.SETTINGS.DATABASES)
        db.connection = db.connections[db.DEFAULT_DB_ALIAS]

        # if we're using gis and sqlite, initialize the database
        if 'django.contrib.gis' in self.INSTALLED_APPS and not self._pg_enabled:
            #db.connection.connection.isolation_level = "EXCLUSIVE"
            curs = db.connection.cursor()
            curs.executescript(open(os.path.join(
                os.path.dirname(__file__),
                'tests', 'sql', 'init_spatialite-2.3.sql')).read())

        # clear model cache
        from django.db.models.loading import cache
        cache.app_store.clear()
        cache.loaded = False
        cache.handled.clear()
        del cache.postponed[:]

        from django.core.management import call_command
        stderr = sys.stderr
        try:
            sys.stderr = StringIO()
            try:
                call_command('syncdb', verbosity=0, interactive=False, database='default')
            except SystemExit:
                self.fail(sys.stderr.getvalue())
            finally:
                sys.stderr = stderr
        except:
            self.tearDown()
            raise

    def tearDown(self):
        super(FunctionalTestCase, self).tearDown()

        from django.db import connections
        for connection in connections.all():
            conn = connection.connection
            connection.close()

        if self._pg_enabled:
            conn = self._pg_connect()
            curs = conn.cursor()
            self._pg_drop_database(curs, self._pg_database_name)

    @property
    def _pg_enabled(self):
        return os.environ.get('WITH_POSTGRESQL', '').lower() in \
               ('1', 'true', 'on', 'yes')

    @property
    def _pg_database_name(self):
        return type(self).__name__.lower()

    def _pg_get_table_names(self, cursor):
        cursor.execute("select table_name as name from information_schema.tables "
                       "where table_schema='public' and table_type != 'VIEW' and "
                       "table_name NOT LIKE 'pg_ts_%%'")

        tables = [result[0] for result in cursor.fetchall()]
        for table in tables:
            if not table.startswith('pg_'):
                yield table

    def _pg_connect(self, name="postgres", autocommit=True):
        from psycopg2 import connect
        conn = connect("dbname=%s" % name)
        if autocommit:
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn

    def _pg_create_database(self):
        owner = os.getlogin()
        name = self._pg_database_name

        from psycopg2 import ProgrammingError

        postgres = self._pg_connect()
        try:
            curs = postgres.cursor()
            self._pg_drop_database(curs, name)

            if 'django.contrib.gis' in self.INSTALLED_APPS:
                template = 'template_postgis'
                try:
                    conn = self._pg_connect(template)
                except ProgrammingError:
                    self.fail("Database template not found: %s." % template)
                conn.close()

                curs.execute("create database %s template %s" % (name, template))
                curs.execute("alter database %s owner to %s" % (name, owner))
            else:
                curs.execute("create database %s" % name)
        finally:
            postgres.close()

        if 'django.contrib.gis' in self.INSTALLED_APPS:
            engine = 'django.contrib.gis.db.backends.postgis'
        else:
            engine = 'django.db.backends.postgresql_psycopg2'

        return {
            'ENGINE': engine,
            'NAME': name,
            }

    def _pg_drop_database(self, postgres, name):
        from psycopg2 import OperationalError
        from psycopg2 import ProgrammingError
        try:
            conn = self._pg_connect(name)
        except OperationalError:
            return False
        except ProgrammingError, exc:
            self.fail(format_exc(exc))

        try:
            curs = conn.cursor()
            for table in self._pg_get_table_names(curs):
                try:
                    curs.execute("drop table %s cascade" % table)
                except ProgrammingError:
                    conn.rollback()
                else:
                    conn.commit()
        finally:
            conn.close()

        postgres.execute("drop database %s" % name)
        return True
