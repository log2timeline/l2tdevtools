#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the git helper."""

from __future__ import unicode_literals

import unittest

import l2tdevtools.helpers.git as git_helper


class GitHelperTest(unittest.TestCase):
  """Tests the git helper"""

  def testInitialize(self):
    """Tests that the helper can be initialized."""
    helper = git_helper.GitHelper(
        u'https://github.com/log2timeline/l2tdevtools.git')
    self.assertIsNotNone(helper)


if __name__ == '__main__':
  unittest.main()
