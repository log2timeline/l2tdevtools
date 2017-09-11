# -*- coding: utf-8 -*-
"""Tests for command line helper."""
import unittest

from l2tdevtools.helpers import cli as cli_helper


class CLIHelperTest(unittest.TestCase):
  """Tests the command line helper"""

  def testRunCommand(self):
    """Tests that the helper can be initialized."""
    mock_responses = {u'echo hi': [0, b'hi\n', b'']}
    test_helper = cli_helper.CLIHelper(mock_responses=mock_responses)
    with self.assertRaises(AttributeError):
      test_helper.RunCommand(u'echo hello')
    exit_code, stdout, stderr = test_helper.RunCommand(u'echo hi')
    self.assertEqual(exit_code, 0)
    self.assertEqual(stdout, b'hi\n')
    self.assertEqual(stderr, b'')

    real_helper = cli_helper.CLIHelper()
    exit_code, stdout, stderr = real_helper.RunCommand(u'echo hello')
    self.assertEqual(exit_code, 0)
    self.assertEqual(stdout, b'hello\n')
    self.assertEqual(stderr, b'')
