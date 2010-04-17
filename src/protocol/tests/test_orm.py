from ..testing import FunctionalTestCase

class HandlerTest(FunctionalTestCase):
    def test_user_messages(self):
        from router.orm import Session
        session = Session()

        from ..models import User
        from ..messages import UserMessage
        user = User(number="123")
        message = UserMessage(text=u"test", sender=user.number)

        session.add(user)
        session.add(message)
        session.flush()

        self.assertEqual(message.user, user)
        self.assertEqual(
            tuple(user.messages), (message,))
