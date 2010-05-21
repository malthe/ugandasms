import datetime

from router.testing import FunctionalTestCase
from router.testing import UnitTestCase

class ParserTest(UnitTestCase):
    @staticmethod
    def _muac(text):
        from ..models import Muac
        from router.parser import Parser
        parser = Parser((Muac,))
        return parser(text)[1]

    @property
    def _datetime(self):
        from datetime import datetime
        return datetime

    @property
    def _timedelta(self):
        from datetime import timedelta
        return timedelta

    def test_empty(self):
        from router.parser import ParseError
        self.assertRaises(ParseError, self._muac, "+muac")

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
        from router.parser import ParseError
        self.assertRaises(ParseError, self._muac, "+muac abc1")

    def test_health_id_with_measurement(self):
        self.assertEqual(self._muac("+muac abc1, 140"), {
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
        from router.parser import ParseError
        try:
            self._muac("+muac foo, m, 31/12/1999, red")
        except ParseError, error:
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

class HandlerTest(FunctionalTestCase): # pragma: NOCOVER
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'health',
        'reporter',
        )

    def setUp(self):
        super(HandlerTest, self).setUp()

        from health.models import Patient
        self.patient = Patient(health_id="bob123", name="Bob")

    @staticmethod
    def _handle(model, uri="test://old", text="", **kwargs):
        time = datetime.datetime(1999, 12, 31, 0, 0, 0)
        from router.models import Peer
        message = model(text=text, time=time)
        message.peer, created = Peer.objects.get_or_create(uri=uri)
        message.peer.save()
        message.save()
        message.handle(**kwargs)
        return message

    @classmethod
    def _register(cls, **kwargs):
        from reporter.models import Registration
        return cls._handle(Registration, **kwargs)

    @classmethod
    def _muac(cls, **kwargs):
        from ..models import Muac
        return cls._handle(Muac, **kwargs)

    def test_patient_record(self):
        self._register(name='ann')
        self._muac(health_id='bob123', 'category': 'g')

        from health.models import Malnutrition
        self.assertTrue(Malnutrition.objects.count(), 1)
        self.assertEqual(Malnutrition.objects.get().patient, self.patient)

    def test_malnutrition_category_reading(self):
        self._register(name='ann')
        self._muac(name='bob', 'category': 'g')

        from health.models import Malnutrition
        self.assertTrue(Malnutrition.objects.count(), 1)
        self.assertEqual(Malnutrition.objects.get().category, 'G')
        self.assertEqual(Malnutrition.objects.get().reading, None)
