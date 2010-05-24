from router.testing import UnitTestCase

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

    def test_patient_id(self):
        self.assertEqual(self._muac("+muac abc1, red"), {
            'patient_id': 'abc1',
            'reading': u'R',
            })

    def test_patient_id_first(self):
        self.assertEqual(self._muac("abc1 +muac red"), {
            'patient_id': 'abc1',
            'reading': u'R',
            })

    def test_patient_id_without_reading(self):
        from router.router import FormatError
        self.assertRaises(FormatError, self._muac, "+muac abc1")

    def test_patient_id_with_measurement(self):
        self.assertEqual(self._muac("+muac abc1, 140"), {
            'patient_id': 'abc1',
            'reading': 140,
            })

    def test_patient_id_with_measurement_in_mm(self):
        self.assertEqual(self._muac("+muac abc1, 140mm"), {
            'patient_id': 'abc1',
            'reading': 140,
            })

    def test_patient_id_with_measurement_in_cm(self):
        self.assertEqual(self._muac("+muac abc1, 14cm"), {
            'patient_id': 'abc1',
            'reading': 140,
            })

    def test_name_sex_age(self):
        self.assertEqual(self._muac("+muac foo, m, 6 days, red"), {
            'name': 'foo',
            'sex': u'M',
            'age': self._timedelta(6),
            'reading': u'R',
            })

    def test_name_sex_age_as_date(self):
        self.assertEqual(self._muac("+muac foo, m, 12/31/1999, red"), {
            'name': 'foo',
            'sex': u'M',
            'age': self._datetime(1999, 12, 31),
            'reading': u'R',
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
            'reading': u'R',
            })

    def test_name_sex_age_with_age_unit(self):
        self.assertEqual(self._muac("+muac foo, m, 6 years, red"), {
            'name': 'foo',
            'sex': u'M',
            'age': self._timedelta(days=6*365),
            'reading': u'R',
            })

        self.assertEqual(self._muac("+muac foo, m, 6 months, red"), {
            'name': 'foo',
            'sex': u'M',
            'age': self._timedelta(days=6*30),
            'reading': u'R',
            })

        self.assertEqual(self._muac("+muac foo, m, 6 weeks, red"), {
            'name': 'foo',
            'sex': u'M',
            'age': self._timedelta(days=6*7),
            'reading': u'R',
            })

    def test_patient_id_with_tag(self):
        self.assertEqual(self._muac("+muac abc1, red, oedema"), {
            'patient_id': 'abc1',
            'reading': 'R',
            'tags': ['oedema'],
            })

    def test_patient_id_with_multiple_tags(self):
        self.assertEqual(self._muac("+muac abc1, red, oedema sick"), {
            'patient_id': 'abc1',
            'reading': 'R',
            'tags': ['oedema', 'sick'],
            })
