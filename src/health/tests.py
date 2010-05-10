from router.testing import UnitTestCase

class ParserTest(UnitTestCase):
    def test_signup(self):
        from health.models import Signup
        from picoparse import run_parser
        self.assertEquals(
            run_parser(Signup.parse, "+vht 123")[0],
            {'role': u'VHT',
             'facility': 123,
             })

    def test_signup_missing_hmis(self):
        from health.models import Signup
        from router.parser import ParseError
        from picoparse import run_parser
        self.assertRaises(ParseError, run_parser, Signup.parse, "+vht")
