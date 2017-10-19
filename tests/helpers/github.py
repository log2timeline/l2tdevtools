#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the GitHub helper."""

from __future__ import unicode_literals

import unittest

from l2tdevtools.helpers import github

from tests.helpers import test_lib


class GitHubHelperTest(unittest.TestCase):
  """Tests the command line helper"""

  # pylint: disable=protected-access

  def testCreatePullRequest(self):
    """Tests the CreatePullRequest function."""
    helper = github.GitHubHelper(
        organization='test', project='test_project')
    helper._url_lib_helper = test_lib.TestURLLibHelper()

    result = helper.CreatePullRequest(
        'TOKEN', 1, 'origin', 'description')
    self.assertTrue(result)

  def testGetForkGitRepoUrl(self):
    """Tests the GetForkGitRepoUrl function."""
    helper = github.GitHubHelper(
        organization='test', project='test_project')
    helper._url_lib_helper = test_lib.TestURLLibHelper()

    expected_url = u'https://github.com/test_user/test_project.git'
    url = helper.GetForkGitRepoUrl('test_user')
    self.assertEqual(url, expected_url)

  def testQueryUser(self):
    """Tests the QueryUser function."""
    helper = github.GitHubHelper(
        organization='test', project='test_project')
    helper._url_lib_helper = test_lib.TestURLLibHelper()

    result = helper.QueryUser('test_user')
    self.assertIsNone(result)


if __name__ == '__main__':
  unittest.main()
