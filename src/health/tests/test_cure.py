from router.testing import UnitTestCase
from .base import Scenario

class ParserTest(UnitTestCase):
    @staticmethod
    def _cure(text):
        from ..models import Cure
        return Cure.parse(text)[0]

    def test_empty(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._cure, "+cure")

    def test_single(self):
        self.assertEqual(self._cure("+cure abc123")['tracking_ids'],
                         ['ABC123'])

    def test_multiple(self):
        self.assertEqual(self._cure("+cure abc123 def456")['tracking_ids'],
                         ['ABC123', 'DEF456'])

class FormTest(Scenario):
    @classmethod
    def _cure(cls, **kwargs):
        from ..models import Cure
        return cls.handle(Cure, **kwargs)

    @classmethod
    def _register(cls, **kwargs):
        from reporter.models import Registration
        return cls.handle(Registration, **kwargs)

    def test_not_exist(self):
        form = self._cure(tracking_ids=["TRACK456"])
        self.assertTrue('TRACK456' in form.replies.get().text)

    def test_not_found(self):
        form = self._cure(tracking_ids=["TRACK456"])
        from ..models import Case
        self.assertEqual(Case.objects.get().closed, None)
        self.assertTrue('TRACK456' in form.replies.get().text)

    def test_single_is_closed(self):
        self._cure(tracking_ids=["TRACK123"])
        from ..models import Case
        self.assertNotEqual(Case.objects.get().closed, None)

    def test_single_yields_two_replies(self):
        self._register(uri="test://other")
        form = self._cure(uri="test://other", tracking_ids=["TRACK123"])
        self.assertEqual(form.replies.count(), 2)

