#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the yapf helper."""

from __future__ import unicode_literals

import unittest

from l2tdevtools.review_helpers import yapf


class YapfHelperTest(unittest.TestCase):
  """Tests the yapf helper"""

  def testInitialize(self):
    """Tests that the helper can be initialized."""
    helper = yapf.YapfHelper()
    self.assertIsNotNone(helper)


if __name__ == '__main__':
  unittest.main()
