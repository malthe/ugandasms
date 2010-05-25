from router.testing import UnitTestCase
from router.testing import FormTestCase

class ParserTest(UnitTestCase):
    @staticmethod
    def _muac(text):
        from ..models import Muac
        return Muac.parse(text)[0]

    @property
    def _datetime(self):
        from datetime import datetime
        return datetime

    @property
    def _timedelta(self):
        from datetime import timedelta
        return timedelta

    def test_empty(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._muac, "+muac")

    def test_health_id(self):
        self.assertEqual(self._muac("+muac abc1, red"), {
            'health_id': 'abc1',
            'category': u'R',
            })

    def test_health_id_first(self):
        self.assertEqual(self._muac("abc1 +muac red"), {
            'health_id': 'abc1',
            'category': u'R',
            })

    def test_health_id_without_reading(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._muac, "+muac abc1")

    def test_health_id_with_measurement(self):
        self.assertEqual(self._muac("+muac abc1, 140"), {
            'health_id': 'abc1',
            'reading': 140,
            })

    def test_health_id_with_implict_cm_measurement(self):
        self.assertEqual(self._muac("+muac abc1, 14"), {
            'health_id': 'abc1',
            'reading': 140,
            })

    def test_health_id_with_measurement_in_mm(self):
        self.assertEqual(self._muac("+muac abc1, 140mm"), {
            'health_id': 'abc1',
            'reading': 140,
            })

    def test_health_id_with_measurement_in_cm(self):
        self.assertEqual(self._muac("+muac abc1, 14cm"), {
            'health_id': 'abc1',
            'reading': 140,
            })

    def test_missing_information(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._muac, "+muac foo")
        self.assertRaises(FormatError, self._muac, "+muac foo, m")
        self.assertRaises(FormatError, self._muac, "+muac foo, m, 16y")

    def test_name_sex_age(self):
        self.assertEqual(self._muac("+muac foo, m, 6 days, red"), {
            'name': 'foo',
            'sex': u'M',
            'age': self._timedelta(6),
            'category': u'R',
            })

    def test_name_sex_age_as_date(self):
        self.assertEqual(self._muac("+muac foo, m, 12/31/1999, red"), {
            'name': 'foo',
            'sex': u'M',
            'age': self._datetime(1999, 12, 31),
            'category': u'R',
            })

    def test_name_sex_wrong_date(self):
        from router.router import FormatError
        try:
            self._muac("+muac foo, m, 31/12/1999, red")
        except FormatError, error:
            self.assertTrue('31/12/1999' in error.text, error.text)
        else: # pragma: NOCOVER
            self.fail()

    def test_name_sex_age_with_sex_female(self):
        self.assertEqual(self._muac("+muac foo, f, 6 days, red"), {
            'name': 'foo',
            'sex': u'F',
            'age': self._timedelta(days=6),
            'category': u'R',
            })

    def test_name_sex_age_with_age_unit(self):
        self.assertEqual(self._muac("+muac foo, m, 6 years, red"), {
            'name': 'foo',
            'sex': u'M',
            'age': self._timedelta(days=6*365),
            'category': u'R',
            })

        self.assertEqual(self._muac("+muac foo, m, 6 months, red"), {
            'name': 'foo',
            'sex': u'M',
            'age': self._timedelta(days=6*30),
            'category': u'R',
            })

        self.assertEqual(self._muac("+muac foo, m, 6 weeks, red"), {
            'name': 'foo',
            'sex': u'M',
            'age': self._timedelta(days=6*7),
            'category': u'R',
            })

    def test_health_id_with_tag(self):
        self.assertEqual(self._muac("+muac abc1, red, oedema"), {
            'health_id': 'abc1',
            'category': 'R',
            'tags': ['oedema'],
            })

    def test_health_id_with_multiple_tags(self):
        self.assertEqual(self._muac("+muac abc1, red, oedema sick"), {
            'health_id': 'abc1',
            'category': 'R',
            'tags': ['oedema', 'sick'],
            })

class FormTest(FormTestCase):
    INSTALLED_APPS = FormTestCase.INSTALLED_APPS + (
        'health',
        'reporter',
        )

    def _create_patient(self):
        from reporter.models import Reporter
        user = Reporter.objects.get()
        from health.models import Patient
        from datetime import datetime
        patient = self.patient = Patient(
            health_id="bob123",
            name="Bob Smith",
            sex='M',
            birthdate=datetime(1980, 1, 1, 3, 42),
            last_reported_on_by=user)
        patient.save()

    @classmethod
    def _register(cls, **kwargs):
        from reporter.models import Registration
        return cls.handle(Registration, **kwargs)

    @classmethod
    def _muac(cls, **kwargs):
        from ..models import Muac
        return cls.handle(Muac, **kwargs)

    def test_patient_green_reading(self):
        self._register(name='ann')
        self._create_patient()
        form = self._muac(health_id='bob123', category='G')
        self.assertTrue('normal' in form.replies.get().text)

    def test_patient_yellow_reading(self):
        self._register(name='ann')
        self._create_patient()
        form = self._muac(health_id='bob123', category='Y')
        self.assertTrue('risk' in form.replies.get().text.lower())
        from ..models import Case
        case = Case.objects.get()
        self.assertEqual(case.patient, self.patient)
        self.assertTrue(case.tracking_id in form.replies.get().text)

    def test_patient_red_reading(self):
        self._register(name='ann')
        self._create_patient()
        form = self._muac(health_id='bob123', category='R')
        self.assertTrue('acute' in form.replies.get().text.lower())
        from ..models import Case
        case = Case.objects.get()
        self.assertEqual(case.patient, self.patient)
        self.assertTrue(case.tracking_id in form.replies.get().text)

    def test_patient_reading_categorization(self):
        self._register(name='ann')
        self._create_patient()
        for reading, category in ((140, 'G'), (125, 'Y'), (110, 'R')):
            self._muac(health_id='bob123', reading=reading)
            from health.models import MuacMeasurement
            report = MuacMeasurement.objects.all()[0]
            self.assertEqual(report.category, category)

    def test_patient_age_is_datetime(self):
        self._register(name='ann')
        from datetime import datetime
        age = datetime(1980, 1, 1, 3, 42)
        self._muac(name="Barbra Smith", age=age, sex='F', reading=140)
        from health.models import MuacMeasurement
        self.assertTrue(MuacMeasurement.objects.get().patient.birthdate, age)

    def test_patient_age_is_timedelta(self):
        self._register(name='ann')
        from datetime import timedelta
        age = timedelta(days=60)
        self._muac(name="Barbra Smith", age=age, sex='F', reading=140)
        from health.models import MuacMeasurement
        self.assertTrue(MuacMeasurement.objects.get().patient.age, age)

    def test_patient_age_is_timedelta_and_less_than_a_month(self):
        self._register(name='ann')
        from datetime import timedelta
        age = timedelta(days=29)
        form = self._muac(name="Barbra Smith", age=age, sex='F', reading=140)
        self.assertTrue('infant' in form.replies.get().text)

    def test_patient_not_found(self):
        from health.models import MuacMeasurement
        self.assertEqual(MuacMeasurement.objects.count(), 0)
        self._register(name='ann')
        self._create_patient()
        form = self._muac(health_id='bob456', reading=140)
        self.assertEqual(MuacMeasurement.objects.count(), 0)
        self.assertTrue('bob456' in form.replies.get().text)

    def test_patient_is_identified(self):
        self._register(name='ann')
        self._create_patient()
        self._muac(
            name="bob smith", age=self.patient.age, sex='M', reading=140)
        from health.models import MuacMeasurement
        self.assertEqual(MuacMeasurement.objects.count(), 1)
        self.assertEqual(MuacMeasurement.objects.get().patient, self.patient)

    def test_patient_reading_with_tags(self):
        self._register(name='ann')
        self._create_patient()
        form = self._muac(health_id='bob123', category='G', tags=['oedema'])
        self.assertTrue('oedema' in form.replies.get().text.lower())

