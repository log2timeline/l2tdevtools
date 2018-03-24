#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the projects helper."""

from __future__ import unicode_literals

import unittest

from l2tdevtools.review_helpers import projects


class ProjectsHelperTest(unittest.TestCase):
  """Tests the projects helper"""

  # pylint: disable=protected-access

  def testInitialize(self):
    """Tests that the helper can be initialized."""
    helper = projects.ProjectsHelper('/home/plaso/l2tdevtools/review.py')
    self.assertIsNotNone(helper)

  # TODO: add test for version_file_path property
  # TODO: add test for _GetProjectName
  # TODO: add test for _ReadFileContents

  def testGetReviewer(self):
    """Tests the GetReviewer function."""
    author = 'test@example.com'

    reviewer = projects.ProjectsHelper.GetReviewer('l2tdevtools', author)
    self.assertNotEqual(reviewer, author)
    self.assertIn(reviewer, projects.ProjectsHelper._REVIEWERS_DEFAULT)

  def testGetReviewersOnCC(self):
    """Tests the GetReviewersOnCC function."""
    author = 'test@example.com'
    reviewer = 'joachim.metz@gmail.com'

    reviewers_cc = projects.ProjectsHelper.GetReviewersOnCC(
        'l2tdevtools', author, reviewer)
    self.assertNotIn(author, reviewers_cc)
    self.assertNotIn(reviewer, reviewers_cc)
    self.assertIn('log2timeline-dev@googlegroups.com', reviewers_cc)

  # TODO: add test for GetVersion
  # TODO: add test for UpdateDpkgChangelogFile
  # TODO: add test for UpdateAuthorsFile
  # TODO: add test for UpdateVersionFile


if __name__ == '__main__':
  unittest.main()
