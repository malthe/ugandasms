from ..testing import FunctionalTestCase

class PolymorphicTest(FunctionalTestCase):
    def test_polymorphic_message(self):
        from router import models
        message = models.Incoming(text=u"test")
        message.save()
        message = models.Message.objects.get()
        self.failIf(message is None)
        self.failUnless(isinstance(message, models.Incoming))

class MessageTest(FunctionalTestCase):
    def test_user(self):
        from router.models import Message
        message = Message(uri="test://test")
        self.assertEqual(message.user, None)
