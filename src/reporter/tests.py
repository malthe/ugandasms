from router.testing import FunctionalTestCase
from router.testing import UnitTestCase

class ParserTest(UnitTestCase):
    def test_empty(self):
        from .models import Registration
        from picoparse import run_parser

        self.assertEquals(run_parser(Registration.parse, "+reg")[0], None)

    def test_name(self):
        from .models import Registration
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

    def test_user_id(self):
        from .models import Registration
        from picoparse import run_parser

        self.assertEquals(run_parser(Registration.parse, "+reg 123")[0], {
            'user_id': 123})
        self.assertEquals(run_parser(Registration.parse, "+reg #123")[0], {
            'user_id': 123})

        from router.parser import ParseError
        self.assertRaises(ParseError, run_parser, Registration.parse, "+reg #")

class HandlerTest(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'reporter',
        )

    @staticmethod
    def _handle(uri="test://test", text="",**kwargs):
        from .models import Registration
        from router.models import Peer
        message = Registration(text=text)
        message.peer, created = Peer.objects.get_or_create(uri=uri)
        message.peer.save()
        message.save()
        message.handle(**kwargs)
        return message

    def test_initial_registration(self):
        self._handle(name="foo")
        from .models import Reporter
        self.assertEqual(Reporter.objects.get().name, "foo")

    def test_inquire_for_id(self):
        self._handle(name="foo")
        inquiry = self._handle()
        self.assertTrue(str(inquiry.user.id) in inquiry.replies.get().text)

    def test_registration_update(self):
        self._handle(name="foo")
        self._handle(name="bar")
        from .models import Reporter
        self.assertEqual(Reporter.objects.get().name, "bar")

    def test_register_new_device_then_update(self):
        self._handle(name="foo")
        from .models import Reporter
        self.assertEqual(Reporter.objects.count(), 1)
        self._handle(uri="test://new", user_id=Reporter.objects.get().pk)
        self.assertEqual(Reporter.objects.count(), 1)
        self._handle(uri="test://new", name="bar")
        self.assertEqual(Reporter.objects.get().name, "bar")
