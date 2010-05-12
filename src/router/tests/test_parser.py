from router.testing import FunctionalTestCase

class ParserTest(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'router.tests',
        )

    def test_error(self):
        from ..parser import Parser
        from .models import Error
        parser = Parser((Error,))
        message = parser("+error")
        from router.models import NotUnderstood
        self.assertTrue(isinstance(message, NotUnderstood))
        self.assertEquals(message.text, "error")

    def test_broken(self):
        from ..parser import Parser
        from .models import Break
        parser = Parser((Break,))
        message = parser("+break")
        from router.models import Broken
        self.assertTrue(isinstance(message, Broken))
