#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the project helper."""

from __future__ import unicode_literals

import unittest

import l2tdevtools.helpers.project as project_helper


class ProjectHelperTest(unittest.TestCase):
  """Tests the project helper"""

  def testInitialize(self):
    """Tests that the helper can be initialized."""
    helper = project_helper.ProjectHelper('/home/plaso/l2tdevtools/review.py')
    self.assertIsNotNone(helper)


if __name__ == '__main__':
  unittest.main()
