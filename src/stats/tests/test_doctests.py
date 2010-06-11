import re
import doctest

from django.test import TestCase

class ModuleTests(TestCase):
    def __new__(cls, test):
        self = TestCase.__new__(cls)
        return getattr(self, test)()

    def test_models(self):
        from stats import models
        return doctest.DocTestSuite(
            models,
            setUp=lambda suite: self.setUp(),
            tearDown=lambda suite: self.tearDown())
