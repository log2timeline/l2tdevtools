#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for command line helper."""

from __future__ import unicode_literals

import unittest

from l2tdevtools.review_helpers import cli


class CLIHelperTest(unittest.TestCase):
  """Tests the command line helper"""

  def testRunCommand(self):
    """Tests that the helper can be initialized."""
    mock_responses = {'echo hi': [0, b'hi\n', b'']}
    test_helper = cli.CLIHelper(mock_responses=mock_responses)
    with self.assertRaises(AttributeError):
      test_helper.RunCommand('echo hello')
    exit_code, stdout, stderr = test_helper.RunCommand('echo hi')
    self.assertEqual(exit_code, 0)
    self.assertEqual(stdout, b'hi\n')
    self.assertEqual(stderr, b'')

    real_helper = cli.CLIHelper()
    exit_code, stdout, stderr = real_helper.RunCommand('echo hello')
    self.assertEqual(exit_code, 0)
    self.assertEqual(stdout, b'hello\n')
    self.assertEqual(stderr, b'')


if __name__ == '__main__':
  unittest.main()
