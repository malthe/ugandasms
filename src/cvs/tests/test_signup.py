from router.testing import FunctionalTestCase
from router.testing import UnitTestCase

class ParserTest(UnitTestCase):
    @staticmethod
    def _signup(text):
        from ..models import Signup
        from router.parser import Parser
        parser = Parser((Signup,))
        return parser(text)

    def test_code(self):
        model, data = self._signup("+vht 123")
        self.assertEquals(data, {'role': u'VHT', 'code': 123})

    def test_no_code(self):
        from router.parser import ParseError
        self.assertRaises(ParseError, self._signup, "+vht")

class HandlerTest(FunctionalTestCase): # pragma: NOCOVER
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'django.contrib.gis',
        'reporter',
        'cvs',
        )

    @staticmethod
    def _handle(model, uri="test://old", text="", **kwargs):
        from router.models import Peer
        message = model(text=text)
        message.peer, created = Peer.objects.get_or_create(uri=uri)
        message.peer.save()
        message.save()
        message.handle(**kwargs)
        return message

    @classmethod
    def _register(cls, **kwargs):
        from reporter.models import Registration
        return cls._handle(Registration, **kwargs)

    @classmethod
    def _signup(cls, **kwargs):
        from ..models import Signup
        return cls._handle(Signup, **kwargs)

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
