from router.testing import FormTestCase
from router.testing import UnitTestCase

class ParserTest(UnitTestCase):
    @staticmethod
    def _parse(text):
        from .models import Registration
        return Registration.parse(text)[0]

    def test_empty(self):
        self.assertEquals(self._parse("+reg"), {})

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
    INSTALLED_APPS = FormTestCase.INSTALLED_APPS + (
        'reporter',
        )

    @classmethod
    def _register(cls, *args, **kwargs):
        from .models import Registration
        return cls.handle(Registration, *args, **kwargs)

    def test_initial_registration(self):
        self._register(name="foo")
        from .models import Reporter
        self.assertEqual(Reporter.objects.get().name, "foo")

    def test_inquire_for_ident(self):
        self._register(name="foo")
        form = self._register()
        self.assertTrue(str(form.message.ident) in form.replies.get().text)

    def test_inquire_for_ident_but_not_registered(self):
        self._register()
        form = self._register()
        from .models import Reporter
        self.assertEqual(Reporter.objects.count(), 0)
        self.assertFalse(str(form.message.ident) in form.replies.get().text)

    def test_registration_update(self):
        self._register(name="foo")
        self._register(name="bar")
        from .models import Reporter
        self.assertEqual(Reporter.objects.get().name, "bar")

    def test_register_new_device_then_update(self):
        self._register(name="foo")
        from .models import Reporter
        self.assertEqual(Reporter.objects.count(), 1)
        self._register(uri="test://new", ident="old")
        self.assertEqual(Reporter.objects.count(), 1)
        self._register(uri="test://new", name="bar")
        self.assertEqual(Reporter.objects.get().name, "bar")

    def test_register_new_device_but_not_found(self):
        self._register(name="foo")
        from .models import Reporter
        self.assertEqual(Reporter.objects.count(), 1)
        form = self._register(uri="test://new", ident="new")
        self.assertEqual(form.user, None)
        self.assertTrue('new' in form.replies.get().text)
