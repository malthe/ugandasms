from ..testing import FunctionalTestCase

class HandlerTest(FunctionalTestCase):
    def setUp(self):
        from ..dispatch import Handler
        self.queue = []
        self.handler = Handler(self.queue)
        super(HandlerTest, self).setUp()

    def test_message_record(self):
        from ..models import Message
        class Test(Message):
            pass

        self.handler(
            Test(u"test", sender="123", receiver="456"))

        from ..orm import Session
        session = Session()
        results = session.query(Message).all()

        self.assertEquals(len(results), 1)
        self.assertEquals(results[0].text, u"test")
        self.assertEquals(results[0].sender, u"123")
        self.assertEquals(results[0].kind, 'test')
        self.assertEquals(results[0].reply, u"No handler available for message kind ``test``.")
