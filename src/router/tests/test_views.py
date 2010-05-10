import time
import datetime

from ..testing import FunctionalTestCase

class KannelViewTest(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'router.tests',
        )

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

    def test_not_acceptable(self):
        request = self._make_request.get("/")
        response = self._view(request)
        self.assertEqual(response.status_code, "406 Not Acceptable")

    def test_message_record(self):
        request = self._make_request.get("/", {
            'receiver': '123',
            'sender': '456',
            'text': '+echo test',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })

        response = self._view(request)

        from ..models import Message
        results = Message.objects.all()
        self.assertEquals(len(results), 1)
        self.assertEquals(results[0].text, u"test")
        self.assertEquals(results[0].receiver, u"123")
        self.assertEquals(results[0].sender, u"456")
        self.assertEquals(results[0].reply, "".join(response))

    def test_message_delivery_success(self):
        request = self._make_request.get("/", {
            'receiver': '123',
            'sender': '456',
            'text': '+echo test',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })

        response = self._view(request)
        self.assertEqual(response.status_code, 200)

        dlr_url = response.get('X-Kannel-DLR-Url', None)
        self.assertNotEqual(dlr_url, None)

        query_string = dlr_url.split('?')[1]
        delivered = datetime.datetime(2000, 1, 1)

        request = self._make_request.get("?" + query_string.replace(
            '%d', '1').replace('%T', str(time.mktime(delivered.timetuple()))))
        response = self._view(request)
        self.assertEqual("".join(response), "")

        # verify delivery record
        from router.models import Delivery
        delivery = Delivery.objects.get()
        self.assertFalse(delivery is None)
        self.assertEqual(delivery.time, delivered)
        self.assertEqual(delivery.success, True)
