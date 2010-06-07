from router.testing import UnitTestCase
from .base import Scenario

class ParserTest(UnitTestCase):
    @staticmethod
    def _otp(text):
        from ..models import OtpForm
        return OtpForm.parse(text)[0]

    def test_empty(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._otp, "+otp")
        self.assertRaises(FormatError, self._otp, "+otp ")

    def test_single(self):
        self.assertEqual(self._otp("+otp abc123")['ids'],
                         ['ABC123'])

    def test_multiple(self):
        self.assertEqual(self._otp("+otp abc123 def456")['ids'],
                         ['ABC123', 'DEF456'])

class FormTest(Scenario):
    @classmethod
    def _otp(cls, **kwargs):
        from ..models import OtpForm
        return cls.handle(OtpForm, **kwargs)

    def test_not_exist(self):
        self.register_default_user()
        form = self._otp(ids=["TRACK456"])
        self.assertTrue('TRACK456' in form.replies.get().text, form.replies.get().text)

    def test_not_found(self):
        self.register_default_user()
        form = self._otp(ids=["TRACK456"])
        from ..models import Case
        self.assertEqual(Case.objects.get().closed, None)
        self.assertTrue('TRACK456' in form.replies.get().text)

    def test_single_is_not_closed(self):
        self.register_default_user()
        self._otp(ids=["TRACK123"])
        from ..models import Case
        self.assertEqual(Case.objects.get().closed, None)

    def test_single_yields_two_replies(self):
        self.register_default_user()
        form = self._otp(ids=["TRACK123"])
        self.assertEqual(form.replies.count(), 2)

    def test_name_sex_age_unknown_patient(self):
        self.register_default_user()
        from datetime import timedelta
        form = self._otp(name="Jim", sex="M", age=timedelta(days=60))
        self.assertTrue('Jim' in form.replies.all()[0].text)

    def test_name_sex_age_known_patient(self):
        self.register_default_user()
        from datetime import datetime
        form = self._otp(uri="test://ann", name="Bob", sex="M", age=datetime(1980, 1, 1, 3, 42))
        from ..models import Case
        self.assertEqual(Case.objects.get().closed, None)
        self.assertTrue('Bob' in form.replies.all()[0].text)
