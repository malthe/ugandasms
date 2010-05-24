from router.testing import FormTestCase
from router.testing import UnitTestCase

class ParserTest(UnitTestCase):
    @staticmethod
    def _signup(text):
        from ..models import Signup
        return Signup.parse(text)[0]

    def test_code(self):
        data = self._signup("+vht 123")
        self.assertEquals(data, {'role': u'VHT', 'code': 123})

    def test_no_code(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._signup, "+vht")

class FormTest(FormTestCase):
    INSTALLED_APPS = FormTestCase.INSTALLED_APPS + (
        'django.contrib.gis',
        'reporter',
        'cvs',
        )

    @classmethod
    def _register(cls, **kwargs):
        from reporter.models import Registration
        return cls.handle(Registration, **kwargs)

    @classmethod
    def _signup(cls, **kwargs):
        from ..models import Signup
        return cls.handle(Signup, **kwargs)

    def test_signup(self):
        self._register(name="foo")
        from ..models import Facility
        from ..models import Location
        location = Location(name="boo")
        location.save()
        Facility(name="bar", code=123, location=location).save()
        message = self._signup(role="VHT", code=123)
        from ..models import Subscription
        self.assertEqual(Subscription.objects.get().user, message.user)

    def test_signup_bad_facility(self):
        self._register(name="foo")
        message = self._signup(role="VHT", code=123)
        from ..models import Subscription
        self.assertEqual(Subscription.objects.count(), 0)
        self.assertTrue("123" in message.replies.get().text)

    def test_signup_must_be_registered(self):
        self._signup(role="VHT", code=123)
        from ..models import Subscription
        self.assertEqual(Subscription.objects.count(), 0)
