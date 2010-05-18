from router.testing import FunctionalTestCase
from router.testing import UnitTestCase

class ParserTest(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'router.tests',
        )

    def test_error(self):
        from ..parser import Parser
        from ..parser import ParseError
        from .models import Error
        parser = Parser((Error,))
        self.assertRaises(ParseError, parser, "+error")

    def test_remaining(self):
        from ..parser import Parser
        from ..parser import ParseError
        from .models import Hello
        parser = Parser((Hello,))
        model, data, remaining = parser("+hello world")
        self.assertEqual(remaining, ' world')

    def test_no_match(self):
        from ..parser import Parser
        from ..parser import ParseError
        parser = Parser(())
        self.assertRaises(ParseError, parser, "")
