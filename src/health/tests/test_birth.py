from django.test import TestCase
from router.testing import FormTestCase

class ParserTest(TestCase):
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
                         {'name': 'Apio', 'sex': 'F', 'place': 'CLINIC'})

class FormTest(FormTestCase):
    @classmethod
    def _birth(cls, **kwargs):
        from ..models import BirthForm
        return cls.handle(BirthForm, **kwargs)

    def test_birth(self):
        self.register_default_user()
        self._birth(name="Apio", sex="F", place="CLINIC")
        from ..models import BirthReport
        self.assertEqual(BirthReport.objects.count(), 1)
