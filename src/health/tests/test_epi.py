import datetime

from router.testing import FunctionalTestCase
from router.testing import UnitTestCase

class ParserTest(UnitTestCase):
    @staticmethod
    def _epi(text):
        from ..models import Epi
        from router.parser import Parser
        parser = Parser((Epi,))
        return parser(text)[:2]

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

    def test_value_lowercase(self):
        model, data = self._epi("+epi ma 5")
        self.assertEqual(data['aggregates'], {'MA': 5.0})

    def test_negative_value(self):
        from router.parser import ParseError
        self.assertRaises(ParseError, self._epi, "+epi MA -5")

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
        TIME = datetime.datetime(1999, 12, 31, 0, 0, 0)
        from router.models import Peer
        message = model(text=text, time=TIME)
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
    def _epi(cls, **kwargs):
        from ..models import Epi
        return cls._handle(Epi, **kwargs)

    def test_no_reports(self):
        self._register(name="foo")
        message = self._epi(aggregates={})
        from ..models import Aggregate
        self.assertEqual(Aggregate.objects.count(), 0)
        self.assertEqual(message.replies.count(), 1)

    def test_single_report(self):
        self._register(name="foo")
        message = self._epi(aggregates={'MA': 5})
        from ..models import Aggregate
        self.assertEqual(Aggregate.objects.count(), 1)
        self.assertEqual(Aggregate.objects.get().reporter, message.user)
        reply = message.replies.get()
        self.assertTrue('malaria 5' in reply.text)

    def test_follow_up_reports(self):
        self._register(name="foo")
        self._epi(aggregates={'MA': 5})
        update1 = self._epi(aggregates={'MA': 10})
        update2 = self._epi(aggregates={'MA': 8})
        self.assertTrue('malaria 10 (+100%)' in update1.replies.get().text)
        self.assertTrue('malaria 8 (-20%)' in update2.replies.get().text)

    def test_follow_up_zero(self):
        self._register(name="foo")
        self._epi(aggregates={'MA': 5})
        update1 = self._epi(aggregates={'MA': 0})
        update2 = self._epi(aggregates={'MA': 10})
        self.assertTrue(
            'malaria 0 (-5)' in update1.replies.get().text, update1.replies.get().text)
        self.assertTrue(
            'malaria 10 (+10)' in update2.replies.get().text, update2.replies.get().text)

    def test_multiple_reports(self):
        self._register(name="foo")
        message = self._epi(aggregates={'MA': 5, 'TB': 10, 'BD': 2})
        from ..models import Aggregate
        self.assertEqual(Aggregate.objects.count(), 3)
        reply = message.replies.get()
        self.assertTrue(
            'bloody diarrhea (dysentery) 2, malaria 5 and tuberculosis 10' in reply.text)
