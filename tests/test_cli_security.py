import os
import ssl
import unittest
from argparse import ArgumentParser
from unittest import mock

from data_retriever.cli_security import add_password_argument, requests_verify, ssl_context


class CliSecurityTest(unittest.TestCase):
    def test_password_comes_from_the_environment(self):
        with mock.patch.dict(os.environ, {"UPSTRA_PASSWORD": "s3cret"}):
            parser = ArgumentParser()
            add_password_argument(parser, help="vCenter password")
            self.assertEqual(parser.parse_args([]).password, "s3cret")
        with mock.patch.dict(os.environ, {}, clear=True):
            parser = ArgumentParser()
            add_password_argument(parser, help="vCenter password")
            with self.assertRaises(SystemExit):
                parser.parse_args([])

    def test_requests_verification_is_configurable(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(requests_verify())
            self.assertTrue(requests_verify(force=True))
        with mock.patch.dict(os.environ, {"UPSTRA_VERIFY_SSL": "true", "UPSTRA_CA_BUNDLE": "/etc/upstra/ca.pem"}):
            self.assertEqual(requests_verify(), "/etc/upstra/ca.pem")

    def test_ssl_context_follows_the_setting(self):
        with mock.patch.dict(os.environ, {"UPSTRA_VERIFY_SSL": "false"}):
            self.assertEqual(ssl_context().verify_mode, ssl.CERT_NONE)
        with mock.patch.dict(os.environ, {"UPSTRA_VERIFY_SSL": "1"}):
            context = ssl_context()
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            self.assertTrue(context.check_hostname)


if __name__ == "__main__":
    unittest.main()
