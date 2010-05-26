from router.testing import UnitTestCase
from router.testing import FormTestCase

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

class FormTest(FormTestCase):
    INSTALLED_APPS = FormTestCase.INSTALLED_APPS + (
        'health',
        'reporter',
        )

    @classmethod
    def _birth(cls, **kwargs):
        from ..models import BirthForm
        return cls.handle(BirthForm, **kwargs)

    @classmethod
    def _register(cls, **kwargs):
        from reporter.models import Registration
        return cls.handle(Registration, **kwargs)

    def test_birth(self):
        self._register(name="ann")
        self._birth(name="Apio", sex="F", location="CLINIC")
        from ..models import Birth
        self.assertEqual(Birth.objects.count(), 1)
