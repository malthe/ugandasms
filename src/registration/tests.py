from router.testing import FunctionalTestCase
from router.testing import UnitTestCase

class ParserTest(UnitTestCase):
    def test_registration(self):
        from registration.models import Registration
        from picoparse import run_parser

        self.assertEquals(
            run_parser(Registration.parse, "+reg Bob")[0],
            {'name': u'Bob',
             })

        self.assertEquals(
            run_parser(Registration.parse, "+register Bob")[0],
            {'name': u'Bob',
             })

        self.assertEquals(
            run_parser(Registration.parse, "+REG Bob")[0],
            {'name': u'Bob',
             })

    def test_registration_missing_name(self):
        from registration.models import Registration
        from router.parser import ParseError
        from picoparse import run_parser
        self.assertRaises(ParseError, run_parser, Registration.parse, "+register")

class HandlerTest(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'registration',
        )

    def test_init(self):
        from registration.models import Registration
        from router.models import Peer
        message = Registration(name="test")
        message.peer, created = Peer.objects.get_or_create(uri="test://test")
        message.peer.save()
        message.save()
        message.handle()
