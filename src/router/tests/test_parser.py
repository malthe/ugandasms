from router.testing import FunctionalTestCase

class ParserTest(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'router.tests',
        )

    def test_error(self):
        from ..parser import Parser
        from .models import Error
        parser = Parser((Error,))
        model, kwargs = parser("+error")
        from router.models import NotUnderstood
        self.assertTrue(model is NotUnderstood)
        self.assertEquals(kwargs.get('text'), "error")
