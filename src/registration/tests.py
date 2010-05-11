from router.testing import FunctionalTestCase
from router.testing import UnitTestCase

class ParserTest(UnitTestCase):
    def test_registration(self):
        from registration.models import Registration
        from picoparse import run_parser

        self.assertEquals(
            run_parser(Registration.parse, "+reg Bob")[0],
            {'name': u'Bob',
             'location': None,
             })

        self.assertEquals(
            run_parser(Registration.parse, "+register Bob")[0],
            {'name': u'Bob',
             'location': None,
             })

        self.assertEquals(
            run_parser(Registration.parse, "+REG Bob")[0],
            {'name': u'Bob',
             'location': None,
             })

        self.assertEquals(
            run_parser(Registration.parse, "+register Bob, Village")[0],
            {'name': u'Bob',
             'location': u'Village',
             })

    def test_registration_missing_name(self):
        from registration.models import Registration
        from router.parser import ParseError
        from picoparse import run_parser
        self.assertRaises(ParseError, run_parser, Registration.parse, "+register")

