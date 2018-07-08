#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the review helper."""

from __future__ import unicode_literals

import unittest

from l2tdevtools.review_helpers import review

from tests import test_lib


class ReviewHelperTest(test_lib.BaseTestCase):
  """Tests the review helper"""

  def testInitialize(self):
    """Tests that the helper can be initialized."""
    helper = review.ReviewHelper(
        'test', '.', 'https://github.com/log2timeline/l2tdevtools.git',
        'import', 'upstream/master')
    self.assertIsNotNone(helper)

  # TODO: test CheckLocalGitState.
  # TODO: test CheckRemoteGitState.
  # TODO: test Close.
  # TODO: test CreatePullRequest.
  # TODO: test InitializeHelpers.
  # TODO: test Lint.
  # TODO: test Merge.
  # TODO: test PrepareUpdate.
  # TODO: test PullChangesFromFork.
  # TODO: test Test.
  # TODO: test UpdateAuthors.
  # TODO: test UpdateVersion.


if __name__ == '__main__':
  unittest.main()
