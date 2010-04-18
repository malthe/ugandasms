import time
import datetime

from ..testing import FunctionalTestCase

class AppTest(FunctionalTestCase):
    def setUp(self):
        from ..parser import Parser
        from ..run import WSGIApp
        from ..models import Message
        from ..exc import InvalidMessage
        from ..orm import Session
        class Raises(Message):
            def __init__(self, text, **kwargs):
                raise InvalidMessage(text)

        parser = Parser(
            (('^abc$', Message),
             ('^(?P<bad_argument>def)$', Raises),
             ))
        from webob import Response

        def handler(message):
            session = Session()
            session.add(message)
            session.flush()
            return Response(repr(
                (message.sender, message.receiver, message.text, message.kind)))
        self.app = WSGIApp(parser, handler, "http://host")
        super(AppTest, self).setUp()

    def test_not_acceptable(self):
        from webob import Request
        request = Request.blank("/", POST={})
        response = request.get_response(self.app)
        self.assertEqual(response.status, "406 Not Acceptable")

    def test_invalid_message(self):
        from webob import Request
        request = Request.blank("/", POST={
            'receiver': '123',
            'sender': '456',
            'text': 'def',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })
        response = request.get_response(self.app)
        self.assertEqual(
            eval(response.body),
            ('456', '123', 'def', 'invalid'))
        self.assertEqual(response.status, "200 OK")

    def test_valid_message(self):
        from webob import Request
        request = Request.blank("/", POST={
            'receiver': '123',
            'sender': '456',
            'text': 'abc',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })
        response = request.get_response(self.app)
        self.assertEqual(
            eval(response.body),
            ('456', '123', u'abc', None))
        self.assertEqual(response.status, "200 OK")

    def test_message_record(self):
        from webob import Request
        request = Request.blank("/", POST={
            'receiver': '123',
            'sender': '456',
            'text': 'test',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })

        response = request.get_response(self.app)

        from ..orm import Session
        from ..models import Message
        session = Session()
        results = session.query(Message).all()

        self.assertEquals(len(results), 1)
        self.assertEquals(results[0].text, u"test")
        self.assertEquals(results[0].receiver, u"123")
        self.assertEquals(results[0].sender, u"456")
        self.assertEquals(results[0].kind, 'not-understood')
        self.assertEquals(results[0].reply, response.body)

    def test_message_delivery_success(self):
        from webob import Request
        request = Request.blank("/", POST={
            'receiver': '123',
            'sender': '456',
            'text': 'test',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })

        response = request.get_response(self.app)
        self.assertEqual(response.status, "200 OK")

        dlr_url = response.headers.get('X-Kannel-DLR-Url')
        self.assertNotEqual(dlr_url, None)

        query_string = dlr_url.split('?')[1]
        delivered = datetime.datetime(2000, 1, 1)
        request = Request.blank("?" + query_string.replace(
            '%d', '1').replace('%T', str(time.mktime(delivered.timetuple()))))
        request.call_application(self.app)

        # verify delivery record
        from router.orm import Session
        session = Session()
        from router.models import Delivery
        delivery = session.query(Delivery).first()
        self.assertFalse(delivery is None)
        self.assertEqual(delivery.time, delivered)
        self.assertEqual(delivery.success, True)
