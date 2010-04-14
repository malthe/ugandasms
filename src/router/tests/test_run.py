import time
import datetime

from ..testing import FunctionalTestCase

class AppTest(FunctionalTestCase):
    def setUp(self):
        from ..parser import Parser
        from ..run import WSGIApp
        from ..models import Message
        parser = Parser(
            (('^abc$', Message),))
        from webob import Response
        def handler(message):
            return Response(repr(
                (message.sender, message.receiver, message.text)))
        self.app = WSGIApp(parser, handler)
        super(AppTest, self).setUp()

    def test_valid_message(self):
        from webob import Request
        request = Request.blank("/", POST={
            'receiver': '123',
            'sender': '456',
            'text': 'test',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })
        self.assertEqual(
            eval(request.get_response(self.app).body),
            ('456', '123', u'test'))
