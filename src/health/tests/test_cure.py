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
                         ['abc123'])

    def test_multiple(self):
        self.assertEqual(self._cure("+cure abc123 def456")['tracking_ids'],
                         ['abc123', 'def456'])

class FormTest(Scenario):
    @classmethod
    def _cure(cls, **kwargs):
        from ..models import Cure
        return cls.handle(Cure, **kwargs)

    def test_not_exist(self):
        form = self._cure(tracking_ids=["track456"])
        self.assertTrue('track456' in form.replies.get().text)

    def test_single_is_closed(self):
        self._cure(tracking_ids=["track123"])
        from ..models import Case
        self.assertNotEqual(Case.objects.get().closed, None)

    def test_single_yields_two_replies(self):
        form = self._cure(tracking_ids=["track123"])
        self.assertEqual(form.replies.count(), 2)

