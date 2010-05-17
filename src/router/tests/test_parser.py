from router.testing import FunctionalTestCase

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
