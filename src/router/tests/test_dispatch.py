from ..testing import FunctionalTestCase

class HandlerTest(FunctionalTestCase):
    def setUp(self):
        from ..dispatch import Handler
        self.queue = []
        self.handler = Handler(self.queue)
        super(HandlerTest, self).setUp()

    def test_no_handler(self):
        from ..models import Message
        class Test(Message):
            pass

        response = self.handler(
            Test(u"test", sender="123", receiver="456"))

        self.assertTrue("test" in response.body)
