from router.testing import UnitTestCase
from .base import Scenario

class ParserTest(UnitTestCase):
    @staticmethod
    def _death(text):
        from ..models import DeathForm
        return DeathForm.parse(text)[0]

    def test_empty(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._death, "+death")

    def test_missing(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._death, "+death")
        self.assertRaises(FormatError, self._death, "+death apio")
        self.assertRaises(FormatError, self._death, "+death apio, f")
        self.assertRaises(FormatError, self._death, "+death apio, f, other")

    def test_id(self):
        self.assertEqual(self._death("+death abc123"), {'ids': ['ABC123']})

    def test_ids(self):
        self.assertEqual(self._death("+death 123 12ab65"), {
            'ids': ['123', '12AB65']})

    def test_name_sex_age(self):
        from datetime import timedelta
        self.assertEqual(self._death("+death bob, m, 6y"), {
            'name': 'bob',
            'sex': 'M',
            'age': timedelta(6*365),})

class FormTest(Scenario):
    @classmethod
    def _death(cls, **kwargs):
        from ..models import DeathForm
        return cls.handle(DeathForm, **kwargs)

    def test_health_id(self):
        form = self._death(ids=['bob123'])
        from ..models import Case
        self.assertNotEqual(Case.objects.get().closed, None)
        from ..models import Patient
        self.assertNotEqual(Patient.objects.get().deathdate, None)
        self.assertTrue('Bob' in form.replies.all()[0].text)

    def test_case_id(self):
        form = self._death(ids=['TRACK123'])
        from ..models import Case
        self.assertNotEqual(Case.objects.get().closed, None)
        from ..models import Patient
        self.assertNotEqual(Patient.objects.get().deathdate, None)
        self.assertTrue('Bob' in form.replies.all()[0].text)

    def test_case_id_not_exist(self):
        form = self._death(ids=['TRACK456'])
        self.assertTrue('TRACK456' in form.replies.get().text)

    def test_name_sex_age_unknown_patient(self):
        from datetime import timedelta
        form = self._death(name="Jim", sex="M", age=timedelta(days=60))
        self.assertTrue('Jim' in form.replies.all()[0].text)

    def test_name_sex_age_known_patient(self):
        from datetime import datetime
        form = self._death(name="Bob", sex="M", age=datetime(1980, 1, 1, 3, 42))
        from ..models import Case
        self.assertNotEqual(Case.objects.get().closed, None)
        from ..models import Patient
        self.assertNotEqual(Patient.objects.get().deathdate, None)
        self.assertTrue('Bob' in form.replies.all()[0].text)
