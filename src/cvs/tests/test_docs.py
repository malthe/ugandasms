import os
import re
import doctest

from router.testing import FunctionalTestCase

OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)

re_trim = re.compile('[\s\n]+')

def assert_equals(s1, s2, strip=True):
    if strip is True and s1 and s2:
        s1 = re_trim.sub(' ', s1.strip(" \n"))
        s2 = re_trim.sub(' ', s2.strip(" \n"))

    assert s1 == s2, "%s != %s." % (repr(s1), repr(s2))

def assert_contains(s1, s2):
    assert s2 in s1, "%s does not contain %s." % (repr(s1), repr(s2))

class DoctestCase(FunctionalTestCase):
    _assertion_helpers = {
        'assert_equals': assert_equals,
        'assert_contains': assert_contains,
        }

    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'health',
        'registration',
        )

    USER_SETTINGS = {
        'HEALTH_FACILITY_ROLES': {
            'VHT': u"Village Health Team",
            'HCW': u"Health Center Worker",
            'HCS': u"Health Center Surveillance Officer",
            }
        }

    def __new__(cls, test):
        self = object.__new__(cls)
        return getattr(self, test)()

    def test_docs(self):
        self.globs = {}

        # determine test documents
        import pkg_resources
        path = pkg_resources.resource_filename("cvs", "docs")
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
            m, *docs, globs=self.globs,
            setUp=lambda suite: self.setUp(),
            tearDown=lambda suite: self.tearDown())

    def setUp(self):
        super(DoctestCase, self).setUp()

        # setup admin user
        from registration.models import User
        from router.models import Peer
        admin = User(
            id=0,
            name=u"Administrator",
            location="Ministry of Health")

        admin.peers.add(Peer(uri="mobile://256000000000"))
        admin.save()

        # add health clinic
        from health.models import Facility
        patiko = Facility(
            hmis=50864,
            name=u"Patiko Health Clinic",
            location=u"Patiko, Gulu District")

        patiko.save()

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

        # set up parser
        from django.db.models import get_models
        from router.parser import Parser
        parser = Parser(get_models())

        # set up gateway
        from router.testing import Gateway
        gateway = Gateway(parser)

        # set up test subscribers
        from router.testing import Subscriber
        self.globs.update({
            'admin': Subscriber(gateway, u"mobile://256000000000"),
            'jonathan': Subscriber(gateway, u"mobile://256000000001"),
            'sam': Subscriber(gateway, u"mobile://256000000002"),
            'parse': parser,
            })

        self.globs.update(self._assertion_helpers)
