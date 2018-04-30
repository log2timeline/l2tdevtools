#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the netrcfile implementation."""

from __future__ import unicode_literals

import unittest

import l2tdevtools.lib.netrcfile as netrcfile_lib

from tests import test_lib


class UploadHelperTest(test_lib.BaseTestCase):
  """Tests the upload helper"""

  def testInitialize(self):
    """Tests that the netrcfile implementation can be initialized."""
    helper = netrcfile_lib.NetRCFile()
    self.assertIsNotNone(helper)


if __name__ == '__main__':
  unittest.main()
