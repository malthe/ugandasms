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
            def __init__(text, *args, **kwargs):
                raise InvalidMessage("invalid: %s." % text)

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
                (message.sender, message.receiver, message.kind)))
        self.app = WSGIApp(parser, handler)
        super(AppTest, self).setUp()

    def test_invalid_message(self):
        from webob import Request
        request = Request.blank("/", POST={
            'receiver': '123',
            'sender': '456',
            'text': 'def',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })
        self.assertEqual(
            eval(request.get_response(self.app).body),
            ('456', '123', 'invalid'))

    def test_valid_message(self):
        from webob import Request
        request = Request.blank("/", POST={
            'receiver': '123',
            'sender': '456',
            'text': 'abc',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })
        self.assertEqual(
            eval(request.get_response(self.app).body),
            ('456', '123', u'message'))
