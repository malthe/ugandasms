import os
import unittest
import doctest
import functools

from protocol.testing import FunctionalTestCase

OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)

def assert_equals(s1, s2, strip=True):
    if strip is True and s1 and s2:
        s1 = s1.strip()
        s2 = s2.strip()

    assert s1 == s2, "%s != %s." % (repr(s1), repr(s2))

def assert_contains(s1, s2):
    assert s2 in s1, "%s does not contain %s." % (repr(s1), repr(s2))

class DoctestCase(FunctionalTestCase):
    _assertion_helpers = {
        'assert_equals': assert_equals,
        'assert_contains': assert_contains,
        }

    def __new__(cls, test):
        self = object.__new__(cls)
        return getattr(self, test)()

    def test_docs(self):
        class queue(object):
            """Mock queue.

            This class mocks a ``queue.Queue`` object, which allows a
            waiting thread to process the send request.

            The test implementation forwards all requests to the
            gateway, which must have previously 'seen' a message from
            the recipient.
            """

            @staticmethod
            def append(item):
                gateway.forward(*item)

        # set up gateway
        from router.testing import Gateway
        from protocol.patterns import parser
        from protocol.handler import Handler
        handler = Handler(queue)
        gateway = Gateway(parser, handler, u"1234")

        # set up test subscribers
        from router.testing import Subscriber
        globs = {
            'admin': Subscriber(gateway, u"256000000000"),
            'jonathan': Subscriber(gateway, u"256000000001"),
            'sam': Subscriber(gateway, u"256000000002"),
            'parse': parser,
            }

        globs.update(self._assertion_helpers)

        # determine test documents
        import pkg_resources
        path = pkg_resources.resource_filename("docs", ())
        docs = [os.path.join(path, filename)
                for filename in os.listdir(path)
                if filename.endswith('.rst')]
        docs = [path for path in docs if not os.path.isdir(path)]

        # set up manuel test processor
        import manuel.testing
        import manuel.codeblock
        import manuel.doctest
        import manuel.capture
        m = manuel.doctest.Manuel()
        m += manuel.codeblock.Manuel()
        m += manuel.capture.Manuel()

        # create test suite
        return manuel.testing.TestSuite(
            m, *docs, globs=globs,
            setUp=lambda suite: self.setUp(),
            tearDown=lambda sutie: self.tearDown())
