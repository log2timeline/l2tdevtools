# -*- coding: utf-8 -*-
"""Tests for the readthedocs helper."""

import unittest

from l2tdevtools.helpers import readthedocs

from tests.helpers import test_lib


class ReadthedocsHelperTest(unittest.TestCase):
  """Tests the readthedocs helper"""

  # pylint: disable=protected-access

  def testTriggerBuild(self):
    """Tests the TriggerBuild function."""
    helper = readthedocs.ReadTheDocsHelper(project=u'test')
    helper._url_lib_helper = test_lib.TestURLLibHelper()

    result = helper.TriggerBuild()
    self.assertTrue(result)


if __name__ == '__main__':
  unittest.main()
