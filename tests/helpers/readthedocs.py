#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the readthedocs helper."""

from __future__ import unicode_literals

import unittest

from l2tdevtools.helpers import readthedocs

from tests.helpers import test_lib


class ReadthedocsHelperTest(unittest.TestCase):
  """Tests the readthedocs helper"""

  # pylint: disable=protected-access

  def testTriggerBuild(self):
    """Tests the TriggerBuild function."""
    helper = readthedocs.ReadTheDocsHelper(project='test')
    helper._url_lib_helper = test_lib.TestURLLibHelper()

    result = helper.TriggerBuild()
    self.assertTrue(result)


if __name__ == '__main__':
  unittest.main()
