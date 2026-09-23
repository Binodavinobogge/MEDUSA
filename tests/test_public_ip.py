import unittest
from core.public_ip import parse_ip

class PublicIPTests(unittest.TestCase):
    def test_valid_families(self):
        self.assertEqual(parse_ip(b'{"ip":"8.8.8.8"}'),'8.8.8.8')
        self.assertEqual(parse_ip(b'{"ip":"2606:4700:4700::1111"}'),'2606:4700:4700::1111')
    def test_invalid_or_private(self):
        for payload in [b'{}',b'<html>',b'{"ip":"127.0.0.1"}',b'{"ip":"wrong"}']:
            with self.assertRaises((ValueError,KeyError)):parse_ip(payload)
