from router.testing import FormTestCase
from router.testing import FunctionalTestCase

class SignupTestCase(FunctionalTestCase):
    INSTALLED_APPS = FormTestCase.INSTALLED_APPS + (
        'location',
        'reporter',
        'stats',
        'cvs',
        )

    def bootstrap(self):
        from cvs.models import HealthRole
        self.role = HealthRole(slug="test", keyword="test", name="Test")
        self.role.save()

        from location.models import LocationKind
        kind = LocationKind(slug="test")
        kind.save()

        from location.models import Facility
        facility = Facility.add_root(kind=kind, code='1234')

        from location.models import Area
        root = Area.add_root(kind=kind, code='1', name='root')
        root = root.get()

        # this location reports to our facility
        location = root.add_child(
            kind=kind, code='11', name='test', report_to=facility)
        location = location.get()

        # various child locations for testing
        self.area1 = location.add_child(kind=kind, code='111', name='child1')
        self.area2 = location.add_child(kind=kind, code='112', name='child2')
        self.area3 = location.add_child(kind=kind, code='113', name='other')

        location = location.get()

        self.area = location
        self.facility = facility

class ParserTest(SignupTestCase):
    @staticmethod
    def _signup(text):
        from ..models import Signup
        return Signup.parse(text)[0]

    def test_code(self):
        self.bootstrap()
        self.assertEquals(
            self._signup("+test 1234"),
            {'role': self.role, 'facility': self.facility})

    def test_no_code(self):
        self.bootstrap()
        from router.router import FormatError
        self.assertRaises(FormatError, self._signup, "+test")

    def test_wrong_code(self):
        self.bootstrap()
        from router.router import FormatError
        self.assertRaises(FormatError, self._signup, "+test 5678")

    def test_code_and_reporting_location(self):
        self.bootstrap()
        self.assertEquals(
            self._signup("+test 1234, test"),
            {'role': self.role,
             'facility': self.facility,
             'area': self.area,
             })

    def test_code_and_reporting_location_fuzzy_matching(self):
        self.bootstrap()
        self.assertEquals(
            self._signup("+test 1234, test1"),
            {'role': self.role,
             'facility': self.facility,
             'area': self.area,
             })

    def test_code_and_child_location(self):
        self.bootstrap()
        self.assertEquals(
            self._signup("+test 1234, other"),
            {'role': self.role,
             'facility': self.facility,
             'area': self.area3,
             })

    def test_code_and_unknown_location(self):
        self.bootstrap()
        data = self._signup("+test 1234, different")

        from location.models import Area
        area = Area.objects.get(kind__slug="user_added_location")

        self.assertEquals(
            data,
            {'role': self.role,
             'facility': self.facility,
             'area': area,
             })

class FormTest(SignupTestCase, FormTestCase):
    @staticmethod
    def _register(uri="test://ann", name="Ann"):
        from router.models import Reporter
        return Reporter.from_uri(uri, name=name)

    @classmethod
    def _signup(cls, **kwargs):
        kwargs.setdefault("uri", "test://ann")
        from ..models import Signup
        return cls.handle(Signup, **kwargs)

    def test_signup_but_not_a_user(self):
        self.bootstrap()
        self._signup(role=self.role, facility=self.facility, area=self.area)

    def test_signup(self):
        self.bootstrap()
        self._register()
        form = self._signup(role=self.role, facility=self.facility, area=self.area)

        from router.models import Reporter
        reporter = Reporter.objects.get()

        self.assertEqual(reporter, form.reporter)

        from cvs.models import HealthReporter
        reporter = HealthReporter.objects.get()

        self.assertEqual(reporter.area, self.area)
        self.assertEqual(reporter.facility, self.facility)

