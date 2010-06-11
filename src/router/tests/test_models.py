from django.test import TestCase

class MessageTest(TestCase):
    def test_ident(self):
        from router.models import Connection
        connection = Connection(uri="foo://bar")
        self.assertEqual(connection.ident, "bar")

    def test_transport(self):
        from router.models import Connection
        connection = Connection(uri="foo://bar")
        self.assertEqual(connection.transport, "foo")

class OutgoingTest(TestCase):
    def test_is_response(self):
        from router.models import Connection
        conn1 = Connection(uri="test://1")
        conn1.save()
        conn2 = Connection(uri="test://2")
        conn2.save()

        from router.models import Incoming
        from router.models import Outgoing
        from router.models import Form

        incoming = Incoming(connection=conn1)
        incoming.save()

        form = Form(message=incoming)
        form.save()

        response = Outgoing(connection=conn1, in_reply_to=form)
        response.save()
        self.assertTrue(response.is_response())

        alert = Outgoing(connection=conn2, in_reply_to=form)
        alert.save()
        self.assertFalse(alert.is_response())

        unsolicited = Outgoing(in_reply_to=None)
        unsolicited.save()
        self.assertFalse(unsolicited.is_response())

class ConnectionTest(TestCase):
    def test_str(self):
        from router.models import Connection
        connection = Connection(uri="test://123")
        self.assertEqual(str(connection), '123')

class ReporterTest(TestCase):
    def test_str(self):
        from router.models import Reporter
        reporter = Reporter(name="Name")
        self.assertEqual(str(reporter), "Name")

class FormTest(TestCase):
    def test_user(self):
        from router.models import Connection
        connection = Connection(uri="test://test")
        from router.models import Incoming
        message = Incoming(connection=connection)
        from router.models import Form
        form = Form(message=message)
        self.assertEqual(form.reporter, None)

    def test_kind(self):
        from router.models import Form
        form = Form()
        self.assertEqual(form.kind, "form", form.kind)
