import doctest

from router.testing import UnitTestCase

class DocTests(UnitTestCase):
    def __new__(self, test):
        return getattr(self, test)()

    @classmethod
    def test_parser(cls):
        from router import parser
        return doctest.DocTestSuite(parser)

    @classmethod
    def test_models(cls):
        from router import models
        return doctest.DocTestSuite(models)