"""Tests for aioacme.util."""

import unittest

from aioacme import util


class UtilTest(unittest.TestCase):
    def test_rename_key(self):
        actual = {
            'old-key': 123,
            'other-key': 456,
        }
        expected = {
            'new-key': 123,
            'other-key': 456,
        }
        util.rename_key(actual, 'old-key', 'new-key')
        self.assertEqual(expected, actual)

    def test_acme_b64encode(self):
        self.assertEqual('AQID', util.acme_b64encode(b'\x01\x02\x03'))
        # Normally, these would have ='s at the end. ACME omits those.
        self.assertEqual('AQI', util.acme_b64encode(b'\x01\x02'))
        self.assertEqual('AQ', util.acme_b64encode(b'\x01'))
        self.assertIsInstance(util.acme_b64encode(b'\x01'), str)

        # Test that we're using the URL-safe character set:
        self.assertEqual('-_A', util.acme_b64encode(b'\xfb\xf0'))

    def test_acme_b64decode(self):
        self.assertEqual(b'\x01\x02\x03', util.acme_b64decode('AQID'))
        self.assertEqual(b'\xfb\xf0', util.acme_b64decode('-_A'))
