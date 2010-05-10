from router.testing import FunctionalTestCase

class ParseTest(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'health',
        'registration',
        )

    def setUp(self):
        super(ParseTest, self).setUp()
        from ..patterns import patterns
        from router.parser import Parser
        self.parser = Parser(patterns)

    def test_empty(self):
        from router.models import Empty
        message = self.parser("")
        self.assertTrue(isinstance(message, Empty))

    def test_registration(self):
        from registration.models import Registration
        message = self.parser("+register bob user")
        self.assertTrue(isinstance(message, Registration))

    def test_vht_signup(self):
        from health.models import Signup
        message = self.parser("+vht 123")
        self.assertTrue(isinstance(message, Signup))

    def test_hcw_signup(self):
        from health.models import Signup
        message = self.parser("+hcw 123")
        self.assertTrue(isinstance(message, Signup))
