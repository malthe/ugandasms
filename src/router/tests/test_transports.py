import cgi
import datetime
import time
import urllib

from ..testing import FunctionalTestCase

class TransportTest(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'router.tests',
        )

    USER_SETTINGS = {
        'MESSAGES': (
            'tests.Echo',
            'tests.Error',
            'tests.Break',
            'tests.Hello',
            'tests.Improper',
            )
        }

    def test_signals(self):
        from router.transports import get_transport
        from router.transports import pre_parse
        from router.transports import post_parse
        from router.transports import pre_handle
        from router.transports import post_handle

        s1 = []
        s2 = []
        s3 = []
        s4 = []

        def before_parse(sender=None, **kwargs):
            s1.append(sender)
            self.assertEqual(sender.id, None)
        pre_parse.connect(before_parse)

        def after_parse(sender=None, data=None, **kwargs):
            s2.append(sender)
            self.assertTrue(isinstance(data, dict))
            self.assertEqual(sender.id, None)
        post_parse.connect(after_parse)

        def before_handle(sender=None, **kwargs):
            s3.append(sender)
            self.assertEqual(sender.replies.count(), 0)
        pre_handle.connect(before_handle)

        def after_handle(sender=None, **kwargs):
            s4.append(sender)
            self.assertEqual(sender.replies.count(), 1)
        post_handle.connect(after_handle)

        transport = get_transport("dummy")
        transport.incoming("test", "+echo test")

        self.assertTrue(len(s1), 1)
        self.assertTrue(len(s2), 1)
        self.assertTrue(len(s3), 1)
        self.assertTrue(len(s4), 1)

    def test_parse_error(self):
        from router.transports import post_parse

        def check_type(sender=None, data=None, **kwargs):
            from router.models import NotUnderstood
            self.assertTrue(isinstance(sender, NotUnderstood),
                            "Sender was of type: %s." % sender.__class__)
            self.assertTrue(data.get('help'), 'error')
        post_parse.connect(check_type)

        from router.transports import get_transport
        transport = get_transport("dummy")
        transport.incoming("test", "+error")

    def test_message_error(self):
        from router.transports import post_parse

        def check_type(sender=None, data=None, **kwargs):
            from router.models import Broken
            self.assertTrue(isinstance(sender, Broken),
                            "Sender was of type: %s." % sender.__class__)
        post_parse.connect(check_type)

        from router.transports import get_transport
        transport = get_transport("dummy")
        transport.incoming("test", "+break")

    def test_multiple(self):
        from router.transports import post_parse

        parsed = []
        def check(sender=None, data=None, **kwargs):
            from router.tests.models import Hello
            self.assertTrue(isinstance(sender, Hello))
            parsed.append(sender)
        post_parse.connect(check)

        from router.transports import get_transport
        transport = get_transport("dummy")
        transport.incoming("test", "+hello +hello")
        self.assertEqual(len(parsed), 2)

    def test_configuration_error(self):
        from router.transports import post_parse

        def check_type(sender=None, data=None, **kwargs):
            from router.models import Broken
            self.assertTrue(isinstance(sender, Broken),
                            "Sender was of type: %s." % sender.__class__)
        post_parse.connect(check_type)

        from router.transports import get_transport
        transport = get_transport("dummy")

        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            transport.incoming("test", "+improper")

            self.assertEqual(len(w), 1)
            self.assertTrue('ImproperlyConfigured' in str(w[0]))

class KannelTest(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'router.tests',
        )

    USER_SETTINGS = {
        'TRANSPORTS': {
            'dummy': {
                'TRANSPORT': 'router.tests.transports.Dummy',
                },
            'kannel': {
                'TRANSPORT': 'router.transports.Kannel',
                'SMS_URL': 'http://locahost:13013/cgi-bin/sendsms',
                }
            },
        'MESSAGES': (
            'Echo',
            )
        }

    @property
    def _make_request(self):
        from django.test import Client
        from django.core.handlers.wsgi import WSGIRequest

        class RequestFactory(Client):
            """See Django snippet #963."""

            def request(self, **request):
                environ = {
                    'HTTP_COOKIE': self.cookies,
                    'PATH_INFO': '/',
                    'QUERY_STRING': '',
                    'REQUEST_METHOD': 'GET',
                    'SCRIPT_NAME': '',
                    'SERVER_NAME': 'testserver',
                    'SERVER_PORT': 80,
                    'SERVER_PROTOCOL': 'HTTP/1.1',
                }
                environ.update(self.defaults)
                environ.update(request)
                return WSGIRequest(environ)

        return RequestFactory()

    @property
    def _view(self):
        from ..views import kannel
        return kannel

    def test_start(self):
        from router.tests import transports
        reload(transports)

        # transports fire when the incoming message class has been
        # initialized; we explicitly send a signal in this test
        from django.db.models import signals
        from router.models import Incoming
        signals.post_init.send(Incoming)

        from .transports import Dummy
        self.assertEqual(Dummy.name, "dummy")

    def test_not_acceptable(self):
        request = self._make_request.get("/")
        response = self._view(request)
        self.assertEqual(response.status_code, "406 Not Acceptable")

    def test_internal_error(self):
        request = self._make_request.get("/", {
            'sender': '456',
            'text': '+break',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })
        response = self._view(request)
        self.assertEqual(response.status_code, "500 Internal Server Error")

    def test_message_record(self):
        request = self._make_request.get("/", {
            'sender': '456',
            'text': '+echo test',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })

        response = self._view(request)

        from ..models import Incoming
        results = Incoming.objects.all()
        self.assertEquals(len(results), 1)
        self.assertEquals(results[0].text, u"+echo test")
        self.assertEquals(results[0].uri, u"kannel://456")

        from ..models import Outgoing
        results = Outgoing.objects.all()
        self.assertEquals(len(results), 1)
        self.assertEquals(results[0].text, u"test")
        self.assertEquals(results[0].uri, u"kannel://456")

    def test_message_delivery_success(self):
        # set up mock sms service
        from router.transports import get_transport
        kannel = get_transport('kannel')

        request = self._make_request.get("/", {
            'sender': '456',
            'text': '+echo test',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })

        query = {}
        def fetch(request, **kwargs):
            query.update(cgi.parse_qsl(request.get_full_url()))
            class response:
                code = 202
            return response()

        kannel.fetch = fetch
        from django.conf import settings
        settings.TRANSPORTS['kannel']['DLR_URL'] = 'http://localhost'

        response = self._view(request)
        args = urllib.urlencode(query)
        self.assertEqual(response.status_code, 200)

        dlr_url = query.pop('dlr-url', "")
        self.assertNotEqual(dlr_url, None)

        delivery = datetime.datetime(2000, 1, 1)
        request = self._make_request.get(
            dlr_url.replace(
                '%d', '1').replace('%T', str(time.mktime(delivery.timetuple()))) + '&' + args)
        response = self._view(request)
        self.assertEqual("".join(response), "")

        # verify delivery record
        from router.models import Outgoing
        message = Outgoing.objects.get()
        self.assertFalse(message is None)
        self.assertEqual(message.delivery, delivery)
        self.assertEqual(message.delivered, True)
