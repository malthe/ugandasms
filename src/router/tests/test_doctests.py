import re
import doctest

from router.testing import FunctionalTestCase
from router.testing import UnitTestCase

OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)

re_trim = re.compile('[\s\n]+')

def assert_equals(s1, s2, strip=True): # pragma: NOCOVER
    if strip is True and s1 and s2:
        s1 = re_trim.sub(' ', s1.strip(" \n"))
        s2 = re_trim.sub(' ', s2.strip(" \n"))

    assert s1 == s2, "%s != %s." % (repr(s1), repr(s2))

def assert_contains(s1, s2): # pragma: NOCOVER
    assert s2 in s1, "%s does not contain %s." % (repr(s1), repr(s2))

class ModuleTests(UnitTestCase):
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

class DocumentationTest(FunctionalTestCase): # pragma: NOCOVER
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'router',
        'router.tests',
        )

    GLOBS = {
        'assert_equals': assert_equals,
        'assert_contains': assert_contains,
        }

    def __new__(cls, test):
        self = object.__new__(cls)
        self.globs = cls.GLOBS.copy()
        return getattr(self, test)()

    def manuel(func):
        def test(self):
            path = func()

            import manuel.testing
            import manuel.codeblock
            import manuel.doctest
            import manuel.capture
            m = manuel.doctest.Manuel()
            m += manuel.codeblock.Manuel()
            m += manuel.capture.Manuel()

            # create test suite
            return manuel.testing.TestSuite(
                m, path, globs=self.globs,
                setUp=lambda suite: self.setUp(),
                tearDown=lambda suite: self.tearDown())
        return test

    @manuel
    def test_getting_started():
        from pkg_resources import resource_filename
        from os.path import join
        return resource_filename("router", join("..", "..", "docs", "getting_started.rst"))

    def setUp(self):
        super(DocumentationTest, self).setUp()

        # handle additional setup in a try-except and make sure we
        # tear down the test afterwards
        try:
            from router.testing import Gateway
            from router.testing import Peer
            transport = Gateway("gateway")
            self.globs['bob'] = Peer(transport, u"256000000000")
        except:
            self.tearDown()
            raise


    USER_SETTINGS = {
        'TRANSPORTS': {
            'gateway': {
                'TRANSPORT': 'router.testing.Gateway',
                },
            },
        }

