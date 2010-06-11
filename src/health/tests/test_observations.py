from django.test import TestCase
from router.testing import FormTestCase

class HealthTestCase(TestCase):
    def setUp(self):
        super(HealthTestCase, self).setUp()

        from stats.models import ReportKind
        from stats.models import ObservationKind

        kind, created = ReportKind.objects.get_or_create(
            slug="agg", name="Test aggregate observations")
        ObservationKind.objects.get_or_create(
            slug="agg_ma", group=kind, name="malaria")
        ObservationKind.objects.get_or_create(
            slug="agg_bd", group=kind, name="bloody diarrhea")
        ObservationKind.objects.get_or_create(
            slug="agg_tb", group=kind, name="tuberculosis")
        ObservationKind.objects.get_or_create(
            slug="agg_total", group=kind, name="Total")

class ParserTest(HealthTestCase):
    @staticmethod
    def _parse(text):
        from ..models import ObservationForm
        return ObservationForm.parse(text, commands={'agg': 'agg'})[0]

    def test_allowed_commands(self):
        self._parse("+agg")

    def test_empty(self):
        data = self._parse("+agg")
        self.assertEqual(data['observations'], {})

    def test_missing_value(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._parse, "+agg ma")

    def test_duplicate(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._parse, "+agg ma 5 ma 10")

    def test_value(self):
        data = self._parse("+agg MA 5")
        self.assertEqual(data['observations'], {'agg_ma': 5.0})

    def test_values_together(self):
        data = self._parse("+agg MA5 BD1")
        self.assertEqual(data['observations'], {'agg_ma': 5.0, 'agg_bd': 1.0})

    def test_value_lowercase(self):
        data = self._parse("+agg ma 5")
        self.assertEqual(data['observations'], {'agg_ma': 5.0})

    def test_value_with_total(self):
        data = self._parse("+agg 10, ma 5")
        self.assertEqual(data['observations'], {'agg_ma': 5.0})
        self.assertEqual(data['total'], 10)

    def test_negative_value(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._parse, "+agg MA -5")

    def test_values(self):
        data = self._parse("+agg MA 5 TB 10")
        self.assertEqual(data['observations'], {'agg_ma': 5.0, 'agg_tb': 10.0})

    def test_values_with_comma(self):
        data = self._parse("+agg MA 5, TB 10")
        self.assertEqual(data['observations'], {'agg_ma': 5.0, 'agg_tb': 10.0})

    def test_bad_indicator(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._parse, "+agg xx 5.0")

    def test_bad_value(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._parse, "+agg ma five")

class FormTest(HealthTestCase, FormTestCase):
    @classmethod
    def _observations(cls, **kwargs):
        from ..models import ObservationForm

        from stats.models import ReportKind
        kind = ReportKind.objects.get(slug="agg")

        return cls.handle(ObservationForm, kind=kind, **kwargs)

    def test_no_reports(self):
        self.register_default_user()
        from stats.models import Report
        form = self._observations(observations={})
        self.assertEqual(Report.objects.count(), 0)
        self.assertEqual(form.replies.count(), 1)

    def test_single_report(self):
        self.register_default_user()
        message = self._observations(observations={'agg_ma': 5})
        from stats.models import Report
        report = Report.objects.get(kind__slug="agg")
        self.assertEqual(report.observations.count(), 1)
        self.assertEqual(report.source.reporter, message.reporter)
        reply = message.replies.get()
        self.assertTrue('malaria 5' in reply.text)

    def test_with_total(self):
        self.register_default_user()
        message = self._observations(total=10, observations={'agg_ma': 5})
        from stats.models import Report
        report = Report.objects.get(kind__slug="agg")
        self.assertEqual(report.observations.count(), 2)
        self.assertEqual(report.source.reporter, message.reporter)
        self.assertEqual(report.observations.get(
            kind__slug__endswith="_total").value, 10)
        reply = message.replies.get()
        self.assertTrue('malaria 5' in reply.text)

    def test_follow_up_reports(self):
        self.register_default_user()
        self._observations(observations={'agg_ma': 5})
        update1 = self._observations(observations={'agg_ma': 10})
        update2 = self._observations(observations={'agg_ma': 8})
        self.assertTrue('malaria 10 (+100%)' in update1.replies.get().text)
        self.assertTrue('malaria 8 (-20%)' in update2.replies.get().text)

    def test_follow_up_zero(self):
        self.register_default_user()
        self._observations(observations={'agg_ma': 5})
        update1 = self._observations(observations={'agg_ma': 0})
        update2 = self._observations(observations={'agg_ma': 10})
        self.assertTrue(
            'malaria 0 (-5)' in update1.replies.get().text, update1.replies.get().text)
        self.assertTrue(
            'malaria 10 (+10)' in update2.replies.get().text, update2.replies.get().text)

    def test_multiple_reports(self):
        self.register_default_user()
        message = self._observations(
            observations={'agg_ma': 5, 'agg_tb': 10, 'agg_bd': 2})
        from stats.models import Report
        report = Report.objects.get(kind__slug="agg")
        self.assertEqual(report.observations.count(), 3)
        reply = message.replies.get()
        self.assertTrue(
            'bloody diarrhea 2, malaria 5 and tuberculosis 10' in reply.text,
            reply.text)
