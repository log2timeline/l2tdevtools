# -*- coding: utf-8 -*-
"""Tests for the review file implementation."""
import unittest

import l2tdevtools.lib.reviewfile as reviewfile_lib


class ReviewFileTest(unittest.TestCase):
  """Tests the review file implementation."""

  # pylint: disable=protected-access
  def testInitialize(self):
    """Tests that the review file can be initialized."""
    review_file = reviewfile_lib.ReviewFile(u'test')
    self.assertIsNotNone(review_file)
    self.assertIsNone(review_file._contents)
