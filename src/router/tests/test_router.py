from ..testing import FunctionalTestCase

class SequentialRouterTest(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'router.tests',
        )

    USER_SETTINGS = {
        'FORMS': ('Echo', 'Error', 'Hello'),
        }

    def test_signals(self):
        from router.router import pre_parse
        from router.router import post_parse
        from router.router import pre_handle
        from router.router import post_handle

        s1 = []
        s2 = []
        s3 = []
        s4 = []

        def before_parse(sender=None, **kwargs):
            s1.append(sender)
            self.assertNotEqual(sender.id, None)
        pre_parse.connect(before_parse)

        def after_parse(sender=None, error=None, **kwargs):
            s2.append(sender)
            self.assertEqual(error, None)
            self.assertEqual(sender.id, None)
        post_parse.connect(after_parse)

        def before_handle(sender=None, result=None, **kwargs):
            s3.append(sender)
            self.assertTrue(isinstance(result, dict))
            self.assertEqual(sender.replies.count(), 0)
        pre_handle.connect(before_handle)

        def after_handle(sender=None, **kwargs):
            s4.append(sender)
            self.assertEqual(sender.replies.count(), 1)
        post_handle.connect(after_handle)

        from router.router import Sequential
        from router.models import Incoming

        router = Sequential()
        message = Incoming(text="+echo test")
        message.save()
        router.route(message)

        self.assertTrue(len(s1), 1)
        self.assertTrue(len(s2), 1)
        self.assertTrue(len(s3), 1)
        self.assertTrue(len(s4), 1)

    def test_parse_error(self):
        def check(sender=None, error=None, **kwargs):
            from router.tests.models import Error
            self.assertTrue(isinstance(sender, Error),
                            "Sender was of type: %s." % sender.__class__)
            self.assertNotEqual(error, None)
            self.assertTrue(error.text, 'error')
        from router.router import post_parse
        post_parse.connect(check)

        from router.router import Sequential
        from router.models import Incoming

        router = Sequential()
        message = Incoming(text="+error")
        message.save()
        router.route(message)

    def test_multiple(self):
        from router.router import post_parse

        parsed = []
        def check(sender=None, result=None, **kwargs):
            from router.tests.models import Hello
            self.assertTrue(isinstance(sender, Hello))
            parsed.append(sender)
        post_parse.connect(check)

        from router.router import Sequential
        from router.models import Incoming

        router = Sequential()
        message = Incoming(text="+hello +hello")
        message.save()
        router.route(message)

        self.assertEqual(len(message.forms.all()), 2)

