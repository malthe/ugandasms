import unittest

class ParseTest(unittest.TestCase):
    def setUp(self):
        from ..patterns import parser
        self.parser = parser

    def test_empty(self):
        from ..messages import Empty
        message = self.parser("")
        self.assertTrue(isinstance(message, Empty))

