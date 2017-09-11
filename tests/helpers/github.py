# -*- coding: utf-8 -*-
"""Tests for the GitHub helper."""
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
        u'TOKEN', 1, u'origin', u'description')
    self.assertTrue(result)

  def testGetForkGitRepoUrl(self):
    """Tests the GetForkGitRepoUrl function."""
    helper = github.GitHubHelper(
        organization='test', project='test_project')
    helper._url_lib_helper = test_lib.TestURLLibHelper()

    expected_url = u'https://github.com/test_user/test_project.git'
    url = helper.GetForkGitRepoUrl(u'test_user')
    self.assertEqual(url, expected_url)

  def testQueryUser(self):
    """Tests the QueryUser function."""
    helper = github.GitHubHelper(
        organization='test', project='test_project')
    helper._url_lib_helper = test_lib.TestURLLibHelper()

    result = helper.QueryUser(u'test_user')
    self.assertIsNone(result)
