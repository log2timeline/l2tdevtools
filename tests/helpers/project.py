#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the project helper."""

from __future__ import unicode_literals

import unittest

from l2tdevtools.helpers import project

from tests import test_lib


class ProjectHelperTest(test_lib.BaseTestCase):
  """Tests the project helper"""

  # pylint: disable=protected-access

  def testInitialize(self):
    """Tests that the helper can be initialized."""
    helper = project.ProjectHelper('/home/plaso/l2tdevtools/review.py')
    self.assertIsNotNone(helper)

  # TODO: add test for version_file_path property
  # TODO: add test for _GetProjectName
  # TODO: add test for _ReadFileContents

  def testGetReviewer(self):
    """Tests the GetReviewer function."""
    reviewer = project.ProjectHelper.GetReviewer('l2tdevtools', 'test')
    self.assertNotEqual(reviewer, 'test')
    self.assertIn(reviewer, project.ProjectHelper._REVIEWERS_DEFAULT)

  # TODO: add test for GetReviewerUsername
  # TODO: add test for GetVersion
  # TODO: add test for UpdateDpkgChangelogFile
  # TODO: add test for UpdateAuthorsFile
  # TODO: add test for UpdateVersionFile


if __name__ == '__main__':
  unittest.main()
