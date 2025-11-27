#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the project helper."""

import unittest

from l2tdevtools.helpers import project

from tests import test_lib


class ProjectHelperTest(test_lib.BaseTestCase):
  """Tests the project helper."""

  # pylint: disable=protected-access

  def testInitialize(self):
    """Tests that the helper can be initialized."""
    helper = project.ProjectHelper('/home/plaso/l2tdevtools/review.py')
    self.assertIsNotNone(helper)

  # TODO: add test for version_file_path property
  # TODO: add test for _GetProjectName
  # TODO: add test for _ReadFileContents


if __name__ == '__main__':
  unittest.main()
