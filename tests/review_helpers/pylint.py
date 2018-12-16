#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the pylint helper."""

from __future__ import unicode_literals

import unittest

from l2tdevtools.review_helpers import pylint

from tests import test_lib


class PylintHelperTest(test_lib.BaseTestCase):
  """Tests the pylint helper"""

  # pylint: disable=protected-access

  def testInitialize(self):
    """Tests the __init__ function."""
    helper = pylint.PylintHelper()
    self.assertIsNotNone(helper)

  def testGetVersion(self):
    """Tests the _GetVersion function."""
    helper = pylint.PylintHelper()

    version_tuple = helper._GetVersion()
    self.assertNotEqual(version_tuple, (0, 0, 0))

  # TODO: add tests for CheckFiles
  # TODO: add tests for CheckUpToDateVersion
  # TODO: add tests for GetRCFile


if __name__ == '__main__':
  unittest.main()
