from ..testing import FunctionalTestCase

class HandlerTest(FunctionalTestCase):
    def test_polymorphic(self):
        from ..models import Message

        class MyMessage(Message):
            __mapper_args__ = {
                'polymorphic_identity': 'my_message'
                }

        message = MyMessage("test")

        from router.orm import Session
        session = Session()
        session.add(message)
        session.flush()

        message = session.query(Message).first()
        self.failIf(message is None)
        self.failUnless(isinstance(message, MyMessage))
