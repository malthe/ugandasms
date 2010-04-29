from ..testing import FunctionalTestCase

class HandlerTest(FunctionalTestCase):
    def test_polymorphic(self):
        from router import models
        message = models.Incoming(text=u"test")
        message.save()
        message = models.Message.objects.get()
        self.failIf(message is None)
        self.failUnless(isinstance(message, models.Incoming))
