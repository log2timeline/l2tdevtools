#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the yapf helper."""

from __future__ import unicode_literals

import unittest

import l2tdevtools.helpers.yapf as yapf_helper


class YapfHelperTest(unittest.TestCase):
  """Tests the yapf helper"""

  def testInitialize(self):
    """Tests that the helper can be initialized."""
    helper = yapf_helper.YapfHelper()
    self.assertIsNotNone(helper)


if __name__ == '__main__':
  unittest.main()
