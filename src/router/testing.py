import os
import pwd
import sys

from copy import deepcopy
from unittest import TestCase
from traceback import format_exc
from StringIO import StringIO

class Gateway(object):
    """Message gateway.

    Use this transport to test communication between two peers.
    """

    def __new__(cls, *args):
        from router.transports import Message
        cls = type("Gateway", (cls, Message), {})
        return object.__new__(cls)

    def __init__(self, name):
        self._subscribers = {}
        super(Gateway, self).__init__(name)

    def receive(self, sender, text):
        self._subscribers[sender.ident] = sender
        messages = self.incoming(sender.ident, text)
        for message in messages:
            for reply in message.replies.all():
                self.send(reply)

    def send(self, message):
        receiver = self._subscribers[message.ident]
        receiver.receive(message.text)

        # note delivery time
        message.delivery = message.in_reply_to.time
        message.save()

class Peer(object):
    """Network peer.

    Each peer is configured for a :class:`gateway` with a unique ``ident``
    string.
    """

    def __init__(self, gateway, ident):
        self.gateway = gateway
        self.ident = ident
        self._received = []

    def send(self, text):
        """Sends text to gateway."""

        text = text.lstrip("> ")
        assert len(text) <= 160
        self.gateway.receive(self, text)

    def receive(self, text=None):
        """Returns a received message by popping it off the incoming
        stack. If no message was received, the empty string is
        returned.
        """

        if text is None:
            return self._received and self._received.pop(0) or u''
        text = "<<< " + text
        self._received.append(text)

class Settings(object):
    pass

# this is a global!
SETTINGS = Settings()

class UnitTestCase(TestCase):
    """Use this test case for tests which do not require a database."""

    def setUp(self):
        from django.conf import settings
        from django.conf import global_settings

        if not settings.configured:
            settings.configure(SETTINGS)
            SETTINGS.__dict__.update(global_settings.__dict__)

        super(UnitTestCase, self).setUp()

class FunctionalTestCase(UnitTestCase):  # pragma: NOCOVER
    """Use this test case for tests which require a database.

    With PostgreSQL:

        Set the environ variable ``WITH_POSTGRESQL`` to a true value
        to run tests using this backend.

        The user account that runs the test suite must have the
        ``CREATEDB`` privilege. When the test harness creates a test
        database, it uses the naming convention defined by the
        ``_pg_database_name`` property. By default this simply
        lower-cases the class name of the test case.

        For GeoDjango support with PostgreSQL, a PostGIS template with the
        name ``'template_postgis'`` must be installed. If you run the
        tests as a non-superuser, the ``datistemplate`` flag must be set.

    With SQLite:

        No custom configuration needed; Spatialite is also supported
        (just add ``"django.contrib.gis"`` to the apps list).

    """

    INSTALLED_APPS = (
        'django.contrib.contenttypes',
        'router',
        )

    BASE_SETTINGS = {
        'DEBUG': True
        }

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

        SETTINGS.__dict__.update({
            'DATABASES': {
                'default': DATABASE,
                },
            'INSTALLED_APPS': self.INSTALLED_APPS,
            'DLR_URL': 'http://host/kannel',
            })

        SETTINGS.__dict__.update(deepcopy(self.BASE_SETTINGS))
        SETTINGS.__dict__.update(deepcopy(self.USER_SETTINGS))

        # reinitialize connections
        from django import db
        db.connections.__init__(SETTINGS.DATABASES)
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

        import gc
        gc.collect()

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
        try:
            owner = os.getlogin()
        except OSError:
            owner = pwd.getpwuid(os.geteuid())[0]
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
