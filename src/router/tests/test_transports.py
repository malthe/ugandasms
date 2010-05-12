import cgi
import datetime
import time
import urllib

from ..testing import FunctionalTestCase

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
            }
        }

    @property
    def _make_request(self):
        from django.http import HttpRequest
        from django.http import QueryDict

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
        self.assertEquals(results[0].text, u"test")
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
