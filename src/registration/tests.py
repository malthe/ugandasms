from router.testing import FunctionalTestCase

class HandlerTest(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'registration',
        )

    def test_user_messages(self):
        from .models import User
        from router.models import Incoming
        user = User(number="123")
        user.save()

        message = Incoming(text=u"test", user=user)
        message.save()

        from router.models import Message
        message = Message.objects.get()
        self.assertEqual(message.user, user)
        self.assertEqual(
            list(user.messages.all()), [message])
