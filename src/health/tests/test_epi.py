from router.testing import FunctionalTestCase
from router.testing import UnitTestCase

class ParserTest(UnitTestCase):
    @staticmethod
    def _epi(text):
        from ..models import Epi
        from router.parser import Parser
        parser = Parser((Epi,))
        return parser(text)

    def test_empty(self):
        model, data = self._epi("+epi")
        self.assertEqual(data['aggregates'], {})

    def test_missing_value(self):
        from router.parser import ParseError
        self.assertRaises(ParseError, self._epi, "+epi ma")

    def test_duplicate(self):
        from router.parser import ParseError
        self.assertRaises(ParseError, self._epi, "+epi ma 5 ma 10")

    def test_value(self):
        model, data = self._epi("+epi MA 5")
        self.assertEqual(data['aggregates'], {'MA': 5.0})

    def test_values(self):
        model, data = self._epi("+epi MA 5 TB 10")
        self.assertEqual(data['aggregates'], {'MA': 5.0, 'TB': 10.0})

    def test_bad_indicator(self):
        from router.parser import ParseError
        self.assertRaises(ParseError, self._epi, "+epi xx 5.0")

    def test_bad_value(self):
        from router.parser import ParseError
        self.assertRaises(ParseError, self._epi, "+epi ma five")

class HandlerTest(FunctionalTestCase): # pragma: NOCOVER
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'django.contrib.gis',
        'health',
        'reporter',
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

    @classmethod
    def _epi(cls, **kwargs):
        from ..models import Signup
        return cls._handle(Signup, **kwargs)
