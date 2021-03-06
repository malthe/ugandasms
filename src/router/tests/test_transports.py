import cgi
import datetime
import time
import urllib

from ..testing import FunctionalTestCase

class MessageTest(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'router.tests',
        )

    USER_SETTINGS = {
        'MESSAGE_ROUTER': 'router.router.Sequential',
        'FORMS': (
            'BadConfiguration',
            'Broken',
            'Echo',
            )
        }
    
    def test_message_error(self):
        from router.tests.transports import Dummy
        transport = Dummy("dummy")

        from django.conf import settings
        try:
            settings.DEBUG = False
            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                transport.incoming("test", "+break")

            self.assertEqual(len(w), 1)
            self.assertTrue('RuntimeError' in str(w[0]))
        finally:
            settings.DEBUG = True

    def test_configuration_error(self):
        from router.tests.transports import Dummy
        transport = Dummy("dummy")

        from django.conf import settings
        try:
            settings.DEBUG = False
            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                transport.incoming("test", "+bad")

            self.assertEqual(len(w), 1)
            self.assertTrue('ImproperlyConfigured' in str(w[0]))
        finally:
            settings.DEBUG = True

    def test_signals(self):
        from router.transports import pre_route
        from router.transports import post_route

        s1 = []
        s2 = []

        def before_route(sender=None, **kwargs):
            s1.append(sender)
            self.assertEqual(sender.forms.count(), 0)
        pre_route.connect(before_route)

        def after_route(sender=None, **kwargs):
            s2.append(sender)
            self.assertEqual(sender.forms.count(), 1)
        post_route.connect(after_route)

        from router.tests.transports import Dummy
        transport = Dummy("dummy")
        transport.incoming("test", "+echo")

        self.assertTrue(len(s1), 1)
        self.assertTrue(len(s2), 1)

class KannelTest(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'router.tests',
        )

    USER_SETTINGS = {
        'FORMS': (
            'Echo',
            'Broken',
            )
        }

    @staticmethod
    def _make_kannel(fetch=None, **kwargs):
        from router.transports import Kannel
        if fetch is None:
            def fetch(*args, **kwargs):
                from django.http import HttpResponse as Response
                return Response(u"")

        kwargs.setdefault('sms_url', '')
        transport = Kannel("kannel", kwargs)
        transport.fetch = fetch
        return transport

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
    def view(self):
        from ..views import kannel
        return kannel

    def test_not_acceptable(self):
        kannel = self._make_kannel()
        request = self._make_request.get("/")
        response = self.view(request)
        self.assertEqual(response.status_code, "406 Not Acceptable")

    def test_internal_error_production_mode(self):
        kannel = self._make_kannel()
        request = self._make_request.get("/", {
            'sender': '456',
            'text': '+break',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })

        from django.conf import settings
        try:
            settings.DEBUG = False
            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                response = self.view(request)

            self.assertEqual(len(w), 1)
            self.assertTrue('RuntimeError' in str(w[0]))
        finally:
            settings.DEBUG = True
        self.assertEqual(response.status_code, "200 OK")

    def test_internal_error_debug_mode(self):
        kannel = self._make_kannel()
        request = self._make_request.get("/", {
            'sender': '456',
            'text': '+break',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })

        response = self.view(request)
        self.assertEqual(response.status_code, "500 Internal Server Error")

    def test_message_record(self):
        kannel = self._make_kannel()
        request = self._make_request.get("/", {
            'sender': '456',
            'text': '+echo test',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })

        self.view(request)

        from ..models import Incoming
        results = Incoming.objects.all()
        self.assertEquals(len(results), 1)
        self.assertEquals(results[0].text, u"+echo test")
        self.assertNotEqual(results[0].time, None)
        self.assertEquals(results[0].uri, u"kannel://456")

        from ..models import Outgoing
        results = Outgoing.objects.all()
        self.assertEquals(len(results), 1)
        self.assertEquals(results[0].text, u"test")
        self.assertEquals(results[0].uri, u"kannel://456")

    def test_message_delivery_success(self):
        request = self._make_request.get("/", {
            'sender': '456',
            'text': '+echo test',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })

        query = {}
        def fetch(request=None, **kwargs):
            query.update(cgi.parse_qsl(request.get_full_url()))
            class response:
                code = 202
            return response()

        kannel = self._make_kannel(fetch=fetch, dlr_url='http://localhost')
        response = self.view(request)

        self.assertNotEqual(query, {})
        args = urllib.urlencode(query)
        self.assertEqual(response.status_code, '200 OK')

        dlr_url = query.pop('dlr-url', "")
        self.assertNotEqual(dlr_url, None)

        delivery = datetime.datetime(2000, 1, 1)
        request = self._make_request.get(
            dlr_url.replace(
                '%d', '1').replace('%T', str(time.mktime(delivery.timetuple()))) + '&' + args)
        response = self.view(request)
        self.assertEqual("".join(response), "")

        # verify delivery record
        from router.models import Outgoing
        message = Outgoing.objects.get()
        self.assertFalse(message is None)
        self.assertEqual(message.delivery, delivery)
        self.assertEqual(message.delivered, True)
        self.assertEqual(message.sent, True)
