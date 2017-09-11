# -*- coding: utf-8 -*-
"""Tests for the review helper."""
import unittest

import l2tdevtools.helpers.review as review_helper


class ReviewHelperTest(unittest.TestCase):
  """Tests the review helper"""

  def testInitialize(self):
    """Tests that the helper can be initialized."""
    helper = review_helper.ReviewHelper(
        u'test', u'https://github.com/log2timeline/l2tdevtools.git',
        u'import', u'upstream/master')
    self.assertIsNotNone(helper)
