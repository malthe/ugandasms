from router.testing import FunctionalTestCase
from router.testing import UnitTestCase

class ParserTest(UnitTestCase):
    @staticmethod
    def _parse(text):
        from .models import Registration
        from picoparse import run_parser
        return run_parser(Registration.parse, text)[0]

    def test_empty(self):
        self.assertEquals(self._parse("+reg"), {})

    def test_name(self):
        self.assertEquals(self._parse("+reg Bob"), {'name': u'Bob'})
        self.assertEquals(self._parse("+register Bob"), {'name': u'Bob'})
        self.assertEquals(self._parse("+REG Bob"), {'name': u'Bob'})

    def test_ident(self):
        self.assertEquals(self._parse("+reg #123"), {'ident': '123'})
        from router.parser import NoMatch
        self.assertRaises(NoMatch, self._parse, "+reg #")

class HandlerTest(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'reporter',
        )

    @staticmethod
    def _handle(uri="test://old", text="",**kwargs):
        from .models import Registration
        from router.models import Peer
        message = Registration(text=text)
        message.peer, created = Peer.objects.get_or_create(uri=uri)
        message.peer.save()
        message.save()
        message.handle(**kwargs)
        return message

    def test_initial_registration(self):
        self._handle(name="foo")
        from .models import Reporter
        self.assertEqual(Reporter.objects.get().name, "foo")

    def test_inquire_for_ident(self):
        self._handle(name="foo")
        inquiry = self._handle()
        self.assertTrue(str(inquiry.ident) in inquiry.replies.get().text)

    def test_inquire_for_ident_but_not_registered(self):
        self._handle()
        inquiry = self._handle()
        from .models import Reporter
        self.assertEqual(Reporter.objects.count(), 0)
        self.assertFalse(str(inquiry.ident) in inquiry.replies.get().text)

    def test_registration_update(self):
        self._handle(name="foo")
        self._handle(name="bar")
        from .models import Reporter
        self.assertEqual(Reporter.objects.get().name, "bar")

    def test_register_new_device_then_update(self):
        self._handle(name="foo")
        from .models import Reporter
        self.assertEqual(Reporter.objects.count(), 1)
        self._handle(uri="test://new", ident="old")
        self.assertEqual(Reporter.objects.count(), 1)
        self._handle(uri="test://new", name="bar")
        self.assertEqual(Reporter.objects.get().name, "bar")

    def test_register_new_device_but_not_found(self):
        self._handle(name="foo")
        from .models import Reporter
        self.assertEqual(Reporter.objects.count(), 1)
        message = self._handle(uri="test://new", ident="new")
        self.assertEqual(message.replies.get().user, None)
        self.assertTrue('new' in message.replies.get().text)
