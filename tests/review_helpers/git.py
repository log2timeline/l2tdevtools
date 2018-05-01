#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the git helper."""

from __future__ import unicode_literals

import unittest

from l2tdevtools.review_helpers import git

from tests import test_lib


class GitHelperTest(test_lib.BaseTestCase):
  """Tests the git helper"""

  def testInitialize(self):
    """Tests that the helper can be initialized."""
    helper = git.GitHelper(
        u'https://github.com/log2timeline/l2tdevtools.git')
    self.assertIsNotNone(helper)


if __name__ == '__main__':
  unittest.main()
