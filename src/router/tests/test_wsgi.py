from unittest import TestCase

def run_app(settings): # pragma: NOCOVER
    from router.wsgi import make_app_from_settings
    from time import sleep
    make_app_from_settings(settings)
    while True:
        sleep(01)

class WSGITestCase(TestCase):
    def test_hup(self):
        from multiprocessing import Process
        from router.tests import settings

        process = Process(target=run_app, args=(settings,))
        process.start()

        from signal import SIGHUP
        from os import kill
        kill(process.pid, SIGHUP)
        process.join(1.0)

        if process.is_alive(): # pragma: NOCOVER
            process.terminate()
            self.fail("Process did not shut down gracefully.")
        else:
            self.assertTrue(process.exitcode == -SIGHUP)
