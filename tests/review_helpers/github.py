#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the GitHub helper."""

from __future__ import unicode_literals

import json
import unittest

from l2tdevtools.review_helpers import github

from tests import test_lib as shared_test_lib
from tests.review_helpers import test_lib


class GitHubHelperTest(shared_test_lib.BaseTestCase):
  """Tests the command line helper"""

  # pylint: disable=protected-access

  def testAssignPullRequest(self):
    """Tests the AssignPullReview function."""
    helper = github.GitHubHelper(
        organization='test', project='test_project')
    helper._url_lib_helper = test_lib.TestURLLibHelper()

    result = helper.AssignPullRequest(4, 'TOKEN', ['Onager'])

    self.assertTrue(result)

  def testCreatePullRequest(self):
    """Tests the CreatePullRequest function."""
    create_result = json.dumps({"number": 1})

    helper = github.GitHubHelper(
        organization='test', project='test_project')
    helper._url_lib_helper = test_lib.TestURLLibHelper(result=create_result)

    result = helper.CreatePullRequest('TOKEN', 'origin', 'title', 'body')
    self.assertEqual(result, 1)

  def testCreatePullRequestReview(self):
    """Tests the CreatePullRequestReview function."""
    helper = github.GitHubHelper(
        organization='test', project='test_project')
    helper._url_lib_helper = test_lib.TestURLLibHelper()

    result = helper.CreatePullRequestReview(4, 'TOKEN', ['Onager'])

    self.assertTrue(result)

  def testGetForkGitRepoUrl(self):
    """Tests the GetForkGitRepoUrl function."""
    helper = github.GitHubHelper(
        organization='test', project='test_project')
    helper._url_lib_helper = test_lib.TestURLLibHelper()

    expected_url = 'https://github.com/test_user/test_project.git'
    url = helper.GetForkGitRepoUrl('test_user')
    self.assertEqual(url, expected_url)

  # TODO: add tests for GetUsername.

  def testQueryUser(self):
    """Tests the QueryUser function."""
    helper = github.GitHubHelper(
        organization='test', project='test_project')
    helper._url_lib_helper = test_lib.TestURLLibHelper()

    result = helper.QueryUser('test_user')
    self.assertIsNone(result)


if __name__ == '__main__':
  unittest.main()
