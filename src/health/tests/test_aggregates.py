from router.testing import FormTestCase
from router.testing import UnitTestCase

class ParserTest(UnitTestCase):
    @staticmethod
    def _agg(text):
        from ..models import Aggregates
        return Aggregates.parse(text)[0]

    def test_allowed_commands(self):
        self._agg("+agg")
        self._agg("+epi")
        self._agg("+home")

    def test_empty(self):
        data = self._agg("+agg")
        self.assertEqual(data['aggregates'], {})

    def test_missing_value(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._agg, "+agg ma")

    def test_duplicate(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._agg, "+agg ma 5 ma 10")

    def test_value(self):
        data = self._agg("+agg MA 5")
        self.assertEqual(data['aggregates'], {'MA': 5.0})

    def test_values_together(self):
        data = self._agg("+agg MA5 BD1")
        self.assertEqual(data['aggregates'], {'MA': 5.0, 'BD': 1.0})

    def test_value_lowercase(self):
        data = self._agg("+agg ma 5")
        self.assertEqual(data['aggregates'], {'MA': 5.0})

    def test_value_with_total(self):
        data = self._agg("+agg 10, ma 5")
        self.assertEqual(data['aggregates'], {'MA': 5.0})
        self.assertEqual(data['total'], 10)

    def test_negative_value(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._agg, "+agg MA -5")

    def test_values(self):
        data = self._agg("+agg MA 5 TB 10")
        self.assertEqual(data['aggregates'], {'MA': 5.0, 'TB': 10.0})

    def test_values_with_comma(self):
        data = self._agg("+agg MA 5, TB 10")
        self.assertEqual(data['aggregates'], {'MA': 5.0, 'TB': 10.0})

    def test_bad_indicator(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._agg, "+agg xx 5.0")

    def test_bad_value(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._agg, "+agg ma five")

class FormTest(FormTestCase):
    INSTALLED_APPS = FormTestCase.INSTALLED_APPS + (
        'health',
        'reporter',
        )

    @classmethod
    def _register(cls, **kwargs):
        from reporter.models import Registration
        return cls.handle(Registration, **kwargs)

    @classmethod
    def _aggregates(cls, **kwargs):
        from ..models import Aggregates
        return cls.handle(Aggregates, **kwargs)

    def test_no_reports(self):
        self._register(name="foo")
        message = self._aggregates(aggregates={})
        from ..models import Aggregate
        self.assertEqual(Aggregate.objects.count(), 0)
        self.assertEqual(message.replies.count(), 1)

    def test_single_report(self):
        self._register(name="foo")
        message = self._aggregates(aggregates={'MA': 5})
        from ..models import Aggregate
        self.assertEqual(Aggregate.objects.count(), 1)
        self.assertEqual(Aggregate.objects.get().reporter, message.user)
        reply = message.replies.get()
        self.assertTrue('malaria 5' in reply.text)

    def test_with_total(self):
        self._register(name="foo")
        message = self._aggregates(total=10, aggregates={'MA': 5})
        from ..models import Aggregate
        self.assertEqual(Aggregate.objects.count(), 1)
        self.assertEqual(Aggregate.objects.get().reporter, message.user)
        self.assertEqual(Aggregate.objects.get().total, 10)
        reply = message.replies.get()
        self.assertTrue('malaria 5' in reply.text)

    def test_follow_up_reports(self):
        self._register(name="foo")
        self._aggregates(aggregates={'MA': 5})
        update1 = self._aggregates(aggregates={'MA': 10})
        update2 = self._aggregates(aggregates={'MA': 8})
        self.assertTrue('malaria 10 (+100%)' in update1.replies.get().text)
        self.assertTrue('malaria 8 (-20%)' in update2.replies.get().text)

    def test_follow_up_zero(self):
        self._register(name="foo")
        self._aggregates(aggregates={'MA': 5})
        update1 = self._aggregates(aggregates={'MA': 0})
        update2 = self._aggregates(aggregates={'MA': 10})
        self.assertTrue(
            'malaria 0 (-5)' in update1.replies.get().text, update1.replies.get().text)
        self.assertTrue(
            'malaria 10 (+10)' in update2.replies.get().text, update2.replies.get().text)

    def test_multiple_reports(self):
        self._register(name="foo")
        message = self._aggregates(aggregates={'MA': 5, 'TB': 10, 'BD': 2})
        from ..models import Aggregate
        self.assertEqual(Aggregate.objects.count(), 3)
        reply = message.replies.get()
        self.assertTrue(
            'bloody diarrhea (dysentery) 2, malaria 5 and tuberculosis 10' in reply.text)
