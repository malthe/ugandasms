import re
import doctest

from router.testing import FunctionalTestCase

class ModuleTests(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'stats',
        'reporter',
        'location',
        )
     
    def __new__(cls, test):
        self = FunctionalTestCase.__new__(cls)
        return getattr(self, test)()

    def test_models(self):
        from stats import models
        return doctest.DocTestSuite(
            models, 
            setUp=lambda suite: self.setUp(),
            tearDown=lambda suite: self.tearDown())
