from django.test import TestCase
from router.testing import FormTestCase

class ParserTest(TestCase):
    @staticmethod
    def _parse(text):
        from .models import Registration
        return Registration.parse(text)[0]

    def test_empty(self):
        self.assertEquals(self._parse("+reg"), {})

    def test_remaining(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._parse, "+reg, Bob")
        self.assertEquals(self._parse("+reg Bob +reg"), {'name': u'Bob'})

    def test_name(self):
        self.assertEquals(self._parse("+reg Bob"), {'name': u'Bob'})
        self.assertEquals(self._parse("+register Bob"), {'name': u'Bob'})
        self.assertEquals(self._parse("+REG Bob"), {'name': u'Bob'})

    def test_ident(self):
        self.assertEquals(self._parse("+reg #123"), {'ident': '123'})
        self.assertEquals(self._parse("+reg 123"), {'ident': '123'})
        self.assertEquals(self._parse("+reg 1-2-3"), {'ident': '123'})
        self.assertEquals(self._parse("+reg 1 2 3"), {'ident': '123'})
        self.assertEquals(self._parse("+reg #"), None)

class HandlerTest(FormTestCase):
    @classmethod
    def _register(cls, **kwargs):
        from .models import Registration
        return cls.handle(Registration, **kwargs)

    def test_initial_registration(self):
        self._register(name="foo")
        from router.models import Reporter
        self.assertEqual(Reporter.objects.get().name, "foo")

    def test_report(self):
        self._register(name="foo")
        from stats.models import Observation
        self.assertEqual(Observation.objects.count(), 1)

    def test_inquire_for_ident(self):
        self._register(name="foo")
        form = self._register()
        self.assertTrue(str(form.message.connection.ident) in form.replies.get().text)

    def test_inquire_for_ident_but_not_registered(self):
        self._register()
        form = self._register()
        from router.models import Reporter
        self.assertEqual(Reporter.objects.count(), 0)
        self.assertFalse(str(form.message.connection.ident) in form.replies.get().text)

    def test_registration_update(self):
        self._register(name="foo")
        self._register(name="bar")
        from router.models import Reporter
        self.assertEqual(Reporter.objects.get().name, "bar")

    def test_register_new_device_then_update(self):
        self._register(name="foo")
        from router.models import Reporter
        self.assertEqual(Reporter.objects.count(), 1)
        self._register(uri="test://new", ident="old")
        self.assertEqual(Reporter.objects.count(), 1)
        self._register(uri="test://new", name="bar")
        self.assertEqual(Reporter.objects.get().name, "bar")

    def test_register_new_device_but_not_found(self):
        self._register(name="foo")
        from router.models import Reporter
        self.assertEqual(Reporter.objects.count(), 1)
        form = self._register(uri="test://new", ident="new")
        self.assertEqual(form.reporter, None)
        self.assertTrue('new' in form.replies.get().text)
