from ..testing import UnitTestCase
from ..testing import FunctionalTestCase

class PolymorphicTest(FunctionalTestCase):
    def test_polymorphic_message(self):
        from router import models
        message = models.Incoming(text=u"test")
        message.save()
        message = models.Message.objects.get()
        self.failIf(message is None)
        self.failUnless(isinstance(message, models.Incoming))

class MessageTest(UnitTestCase):
    def test_ident(self):
        from router.models import Message
        message = Message(uri="foo://bar")
        self.assertEqual(message.ident, "bar")

    def test_transport(self):
        from router.models import Message
        message = Message(uri="foo://bar")
        self.assertEqual(message.transport, "foo")

class FormTest(UnitTestCase):
    def test_user(self):
        from router.models import Peer
        peer = Peer(uri="test://test")
        from router.models import Incoming
        message = Incoming(peer=peer)
        from router.models import Form
        form = Form(message=message)
        self.assertEqual(form.user, None)
