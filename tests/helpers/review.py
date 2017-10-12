# -*- coding: utf-8 -*-
"""Tests for the review helper."""
from __future__ import unicode_literals
import unittest

import l2tdevtools.helpers.review as review_helper


class ReviewHelperTest(unittest.TestCase):
  """Tests the review helper"""

  def testInitialize(self):
    """Tests that the helper can be initialized."""
    helper = review_helper.ReviewHelper(
        'test', '.', 'https://github.com/log2timeline/l2tdevtools.git',
        'import', 'upstream/master')
    self.assertIsNotNone(helper)
