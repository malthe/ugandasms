from django.test import TestCase
from .base import Scenario

class ParserTest(TestCase):
    @staticmethod
    def _cure(text):
        from ..models import CureForm
        return CureForm.parse(text)[0]

    def test_empty(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._cure, "+cure")
        self.assertRaises(FormatError, self._cure, "+cure ")

    def test_single(self):
        self.assertEqual(self._cure("+cure abc123")['ids'],
                         ['ABC123'])

    def test_multiple(self):
        self.assertEqual(self._cure("+cure abc123 def456")['ids'],
                         ['ABC123', 'DEF456'])

class FormTest(Scenario):
    @classmethod
    def _cure(cls, **kwargs):
        from ..models import CureForm
        return cls.handle(CureForm, **kwargs)

    def test_not_exist(self):
        self.register_default_user()
        form = self._cure(ids=["TRACK456"])
        self.assertTrue('TRACK456' in form.replies.get().text, form.replies.get().text)

    def test_not_found(self):
        self.register_default_user()
        form = self._cure(ids=["TRACK456"])
        from ..models import Case
        self.assertEqual(Case.objects.get().closed, None)
        self.assertTrue('TRACK456' in form.replies.get().text)

    def test_single_is_closed(self):
        self.register_default_user()
        self._cure(ids=["TRACK123"])
        from ..models import Case
        self.assertNotEqual(Case.objects.get().closed, None)

    def test_single_yields_two_replies(self):
        self.register_default_user()
        form = self._cure(ids=["TRACK123"])
        self.assertEqual(form.replies.count(), 2)

    def test_name_sex_age_unknown_patient(self):
        self.register_default_user()
        from datetime import timedelta
        form = self._cure(name="Jim", sex="M", age=timedelta(days=60))
        self.assertTrue('Jim' in form.replies.all()[0].text)

    def test_name_sex_age_known_patient(self):
        self.register_default_user()
        from datetime import datetime
        form = self._cure(uri="test://ann", name="Bob", sex="M", age=datetime(1980, 1, 1, 3, 42))
        from ..models import Case
        self.assertNotEqual(Case.objects.get().closed, None)
        self.assertTrue('Bob' in form.replies.all()[0].text)
