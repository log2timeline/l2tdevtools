#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the review script."""

import os
import unittest

from utils import review


class CodeReviewHelperTest(unittest.TestCase):
  """Tests for the codereview helper class."""

  def setUp(self):
    """Sets up a test case."""
    self._codereview_helper = review.CodeReviewHelper(
        u'test@example.com', no_browser=True)

  def testGetXSRFToken(self):
    """Tests the GetXSRFToken function."""
    # Only test if the method completes without errors.
    self._codereview_helper.GetXSRFToken()

  def testQueryIssue(self):
    """Tests the QueryIssue function."""
    codereview_information = self._codereview_helper.QueryIssue(269830043)
    self.assertIsNotNone(codereview_information)

    expected_description = (
        u'Updated review scripts and added Python variant #40')
    description = codereview_information.get(u'subject')
    self.assertEqual(description, expected_description)

    codereview_information = self._codereview_helper.QueryIssue(0)
    self.assertIsNone(codereview_information)

    codereview_information = self._codereview_helper.QueryIssue(1)
    self.assertIsNone(codereview_information)


class GitHelperTest(unittest.TestCase):
  """Tests for the git helper class."""

  _GIT_REPO_URL = b'https://github.com/log2timeline/l2tdevtools.git'

  def setUp(self):
    """Sets up a test case."""
    self._git_helper = review.GitHelper(self._GIT_REPO_URL)

  def testCheckHasBranch(self):
    """Tests the CheckHasBranch function."""
    self.assertTrue(self._git_helper.CheckHasBranch(u'master'))
    self.assertFalse(self._git_helper.CheckHasBranch(u'bogus'))

  def testCheckHasProjectOrigin(self):
    """Tests the CheckHasProjectOrigin function."""
    # Only test if the method completes without errors.
    self._git_helper.CheckHasProjectOrigin()

  def testCheckHasProjectUpstream(self):
    """Tests the CheckHasProjectUpstream function."""
    # Only test if the method completes without errors.
    self._git_helper.CheckHasProjectUpstream()

  def testCheckHasUncommittedChanges(self):
    """Tests the CheckHasUncommittedChanges function."""
    # Only test if the method completes without errors.
    self._git_helper.CheckHasUncommittedChanges()

  def testCheckSynchronizedWithUpstream(self):
    """Tests the CheckSynchronizedWithUpstream function."""
    # Only test if the method completes without errors.
    self._git_helper.CheckSynchronizedWithUpstream()

  def testGetActiveBranch(self):
    """Tests the GetActiveBranch function."""
    active_branch = self._git_helper.GetActiveBranch()
    self.assertIsNotNone(active_branch)

  def testGetChangedFiles(self):
    """Tests the GetChangedFiles function."""
    # Only test if the method completes without errors.
    self._git_helper.GetChangedFiles(u'origin/master')

  def testGetChangedPythonFiles(self):
    """Tests the GetChangedPythonFiles function."""
    # Only test if the method completes without errors.
    self._git_helper.GetChangedPythonFiles(u'origin/master')

  def testGetEmailAddress(self):
    """Tests the GetEmailAddress function."""
    email_address = self._git_helper.GetEmailAddress()
    self.assertIsNotNone(email_address)

  def testGetLastCommitMessage(self):
    """Tests the GetLastCommitMessage function."""
    last_commit_message = self._git_helper.GetLastCommitMessage()
    self.assertIsNotNone(last_commit_message)


class GitHubHelperTest(unittest.TestCase):
  """Tests for the github helper class."""

  def testQueryUser(self):
    """Tests the QueryUser function."""
    github_helper = review.GitHubHelper(u'log2timeline', u'l2tdevtools')

    user_information = github_helper.QueryUser(u'joachimmetz')
    self.assertIsNotNone(user_information)

    expected_name = u'Joachim Metz'
    name = user_information.get(u'name')
    self.assertEqual(name, expected_name)

    user_information = github_helper.QueryUser(
        u'df07128937706371903f6ca7241a73db')
    self.assertIsNone(user_information)


class ProjectHelper(unittest.TestCase):
  """Tests for the project helper class."""

  def testProjectName(self):
    """Tests the project_name attribute."""
    test_path = u'/Users/l2tdevtools/l2tdevtools/utils/review.py'
    project_helper = review.ProjectHelper(test_path)

    self.assertEqual(project_helper.project_name, u'l2tdevtools')

    # Create a new helper, as the project name is cached.
    test_path = u'/Users/l2tdevtools/plaso_master/utils/review.py'
    project_helper = review.ProjectHelper(test_path)

    self.assertEqual(project_helper.project_name, u'plaso')


class PylintHelperTest(unittest.TestCase):
  """Tests for the pylint helper class."""

  def setUp(self):
    """Sets up a test case."""
    self._pylint_helper = review.PylintHelper()

  def testCheckUpToDateVersion(self):
    """Tests the CheckUpToDateVersion function."""
    self.assertTrue(self._pylint_helper.CheckUpToDateVersion())

  def testCheckFiles(self):
    """Tests the CheckFiles function."""
    test_file = os.path.join(u'test_data', u'linter_pass.py')
    self.assertTrue(self._pylint_helper.CheckFiles([test_file]))

    test_file = os.path.join(u'test_data', u'linter_fail.py')
    self.assertFalse(self._pylint_helper.CheckFiles([test_file]))

    # TODO: capture output and compare.


class SphinxAPIDocHelperTest(unittest.TestCase):
  """Tests for the sphinx-apidoc helper class."""

  def setUp(self):
    """Sets up a test case."""
    self._sphinxapidoc_helper = review.SphinxAPIDocHelper(u'plaso')

#  def testCheckUpToDateVersion(self):
#    """Tests the CheckUpToDateVersion function."""
#    self.assertTrue(self._sphinxapidoc_helper.CheckUpToDateVersion())


class NetRCFileTest(unittest.TestCase):
  """Tests for the .netrc file class."""

  def testGetGitHubAccessToken(self):
    """Tests the GetGitHubAccessToken function."""
    # Only test if the method completes without errors.
    netrc_file = review.NetRCFile()
    netrc_file.GetGitHubAccessToken()


class ReviewFileTest(unittest.TestCase):
  """Tests for the review file class."""

  def testCreateUseRemove(self):
    """Tests the Create, GetCodeReviewIssueNumber and Remove functions."""
    # Check if the review file does not already exist.
    review_file_path = os.path.join(u'.review', u'bogus')
    self.assertFalse(os.path.exists(review_file_path))

    review_file = review.ReviewFile(u'bogus')
    review_file.Create(123456789)

    self.assertTrue(os.path.exists(review_file_path))

    review_file = review.ReviewFile(u'bogus')
    codereview_issue_number = review_file.GetCodeReviewIssueNumber()
    self.assertEqual(codereview_issue_number, 123456789)

    review_file = review.ReviewFile(u'bogus')
    review_file.Remove()
    self.assertFalse(os.path.exists(review_file_path))


if __name__ == '__main__':
  unittest.main()
