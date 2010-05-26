from router.testing import UnitTestCase
from .base import Scenario

class ParserTest(UnitTestCase):
    @staticmethod
    def _birth(text):
        from ..models import BirthForm
        return BirthForm.parse(text)[0]

    def test_empty(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._birth, "+birth")

    def test_missing(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._birth, "+birth")
        self.assertRaises(FormatError, self._birth, "+birth apio")
        self.assertRaises(FormatError, self._birth, "+birth apio, f")

    def test_bad_location(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._birth, "+birth api, f, bed")

    def test_birth(self):
        self.assertEqual(self._birth("+birth Apio, female clinic"),
                         {'name': 'Apio', 'sex': 'F', 'location': 'CLINIC'})

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
