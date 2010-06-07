from ..testing import FunctionalTestCase

class SequentialRouterTest(FunctionalTestCase):
    INSTALLED_APPS = FunctionalTestCase.INSTALLED_APPS + (
        'router.tests',
        )

    USER_SETTINGS = {
        'FORMS': ('Echo', 'Error', 'CantParse', 'Hello', 'Broken'),
        }

    def test_signals(self):
        from router.router import pre_handle
        from router.router import post_handle

        s3 = []
        s4 = []

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

        self.assertTrue(len(s3), 1)
        self.assertTrue(len(s4), 1)

    def test_formatting_error_means_dont_handle(self):
        handled = []
        def check(sender=None, **kwargs):
            handled.append(sender) # pragma: NOCOVER
        from router.router import pre_handle
        pre_handle.connect(check)

        from router.router import Sequential
        from router.models import Incoming

        router = Sequential()
        message = Incoming(text="+cantparse")
        message.save()
        router.route(message)
        self.assertEqual(len(handled), 0)

    def test_multiple(self):
        from router.router import post_handle

        parsed = []
        def check(sender=None, result=None, **kwargs):
            from router.tests.models import Hello
            self.assertTrue(isinstance(sender, Hello))
            parsed.append(sender)
        post_handle.connect(check)

        from router.router import Sequential
        from router.models import Incoming

        router = Sequential()
        message = Incoming(text="+hello +hello")
        message.save()
        router.route(message)

        self.assertEqual(len(parsed), 2)

    def test_error(self):
        from router.router import Sequential
        from router.models import Incoming

        router = Sequential()
        message = Incoming(text="+error")
        message.save()
        self.assertRaises(RuntimeError, router.route, message)
