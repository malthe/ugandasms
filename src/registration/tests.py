from router.testing import FunctionalTestCase
from router.testing import UnitTestCase

class ParserTest(UnitTestCase):
    def test_registration(self):
        from registration.models import Registration
        from picoparse import run_parser

        self.assertEquals(
            run_parser(Registration.parse, "+reg Bob")[0],
            {'name': u'Bob',
             'location': None,
             })

        self.assertEquals(
            run_parser(Registration.parse, "+register Bob")[0],
            {'name': u'Bob',
             'location': None,
             })

        self.assertEquals(
            run_parser(Registration.parse, "+REG Bob")[0],
            {'name': u'Bob',
             'location': None,
             })

        self.assertEquals(
            run_parser(Registration.parse, "+register Bob, Village")[0],
            {'name': u'Bob',
             'location': u'Village',
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

    def test_user_messages(self):
        from .models import User
        from router.models import Incoming
        user = User(number="123")
        user.save()

        message = Incoming(text=u"test", user=user)
        message.save()

        from router.models import Message
        message = Message.objects.get()
        self.assertEqual(message.user, user)
        self.assertEqual(
            list(user.messages.all()), [message])
