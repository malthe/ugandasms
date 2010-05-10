from router.testing import FunctionalTestCase

class ParserTest(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'router.tests',
        )

    def test_error(self):
        from ..parser import Parser
        from django.db.models import get_models
        parser = Parser(get_models())
        message = parser("+error")
        from router.models import NotUnderstood
        self.assertTrue(isinstance(message, NotUnderstood))
        self.assertEquals(message.text, "error")

    def test_broken(self):
        from ..parser import Parser
        from django.db.models import get_models
        parser = Parser(get_models())
        message = parser("+break")
        from router.models import Broken
        self.assertTrue(isinstance(message, Broken))
