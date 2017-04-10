#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the review script."""

import os
import unittest

from utils import review


class CLIHelperTest(unittest.TestCase):
  """Tests for the CLI helper functions."""

  def testRunCommand(self):
    """Tests the RunCommand function."""
    cli_helper = review.CLIHelper()

    exit_code, _, _ = cli_helper.RunCommand(u'echo')
    self.assertEqual(exit_code, 0)


class CodeReviewHelperTest(unittest.TestCase):
  """Tests for the codereview helper class."""

  # pylint: disable=protected-access

  def testGetReviewer(self):
    """Tests the _GetReviewer function."""
    author = u'test@example.com'
    codereview_helper = review.CodeReviewHelper(author, no_browser=True)

    reviewer = codereview_helper._GetReviewer()
    self.assertNotEqual(reviewer, author)
    self.assertIn(reviewer, codereview_helper._REVIEWERS)

  def testGetReviewersOnCC(self):
    """Tests the _GetReviewersOnCC function."""
    author = u'test@example.com'
    reviewer = u'joachim.metz@gmail.com'
    codereview_helper = review.CodeReviewHelper(author, no_browser=True)

    reviewers_cc = codereview_helper._GetReviewersOnCC(reviewer)
    self.assertNotIn(author, reviewers_cc)
    self.assertNotIn(reviewer, reviewers_cc)
    self.assertIn(u'log2timeline-dev@googlegroups.com', reviewers_cc)

  # TODO: add AddMergeMessage test.
  # TODO: add CloseIssue test.
  # TODO: add CreateIssue test.
  # TODO: add GetAccessToken test.

  @unittest.skipIf(
      os.environ.get(u'TRAVIS_OS_NAME', u''), 'Travis-CI not supported')
  def testGetXSRFToken(self):
    """Tests the GetXSRFToken function."""
    codereview_helper = review.CodeReviewHelper(
        u'test@example.com', no_browser=True)

    # Only test if the method completes without errors.
    codereview_helper.GetXSRFToken()

  def testQueryIssue(self):
    """Tests the QueryIssue function."""
    codereview_helper = review.CodeReviewHelper(
        u'test@example.com', no_browser=True)

    codereview_information = codereview_helper.QueryIssue(269830043)
    self.assertIsNotNone(codereview_information)

    expected_description = (
        u'Updated review scripts and added Python variant #40')
    description = codereview_information.get(u'subject')
    self.assertEqual(description, expected_description)

    codereview_information = codereview_helper.QueryIssue(0)
    self.assertIsNone(codereview_information)

    codereview_information = codereview_helper.QueryIssue(1)
    self.assertIsNone(codereview_information)

  # TODO: add UpdateIssue test.


class ErrorGitHelper(review.GitHelper):
  """Git command helper for testing that will always error."""

  def RunCommand(self, unused_command):
    """Runs a command.

    Args:
      command (str): command to run.

    Returns:
      tuple[int, bytes, bytes]: exit code, stdout and stderr data.
    """
    return 1, b'', b''


class TestGitHelper(review.GitHelper):
  """Git command helper for testing."""

  _GIT_BRANCH_DATA = (
      b'  cleanup\n'
      b'* feature\n'
      b'  master\n')

  _GIT_EMAIL_DATA = b'username@example.com\n'

  _GIT_LAST_LOG_DATA = (
      b'commit 79a78f3f0044192a0354ad682733a7996c15e89c\n'
      b'Author: User <username@example.com>\n'
      b'Date:   Sat Apr 8 07:44:22 2017 +0200\n'
      b'\n'
      b'    Made changes\n')

  _GIT_REMOTE_DATA = (
      b'origin\thttps://github.com/username/l2tdevtools.git (fetch)\n'
      b'origin\thttps://github.com/username/l2tdevtools.git (push)\n'
      b'upstream\thttps://github.com/log2timeline/l2tdevtools.git (fetch)\n'
      b'upstream\thttps://github.com/log2timeline/l2tdevtools.git (push)\n')

  def RunCommand(self, command):
    """Runs a command.

    Args:
      command (str): command to run.

    Returns:
      tuple[int, bytes, bytes]: exit code, stdout and stderr data.
    """
    if command == u'git branch':
      return 0, self._GIT_BRANCH_DATA, b''

    if command == u'git checkout master':
      return 0, b'', b''

    if command == u'git config user.email':
      return 0, self._GIT_EMAIL_DATA, b''

    if command == u'git log -1':
      return 0, self._GIT_LAST_LOG_DATA, b''

    if command == u'git remote -v':
      return 0, self._GIT_REMOTE_DATA, b''

    if command.startswith(u'git add -A '):
      return 0, b'', b''

    if command.startswith(u'git branch -D '):
      return 0, b'', b''

    if command.startswith(u'git fetch '):
      return 0, b'', b''

    if command.startswith(u'git pull --no-edit '):
      return 0, b'', b''

    if command.startswith(u'git pull --squash '):
      return 0, b'', b''

    if command.startswith(u'git push'):
      return 0, b'', b''


class GitHelperTest(unittest.TestCase):
  """Tests for the git helper class."""

  # pylint: disable=protected-access

  _GIT_REPO_URL = b'https://github.com/log2timeline/l2tdevtools.git'

  def testGetRemotes(self):
    """Tests the _GetRemotes function."""
    git_helper = TestGitHelper(self._GIT_REPO_URL)

    remotes = git_helper._GetRemotes()
    self.assertEqual(len(remotes), 4)

  def testAddPath(self):
    """Tests the AddPath function."""
    git_helper = TestGitHelper(self._GIT_REPO_URL)

    result = git_helper.AddPath(u'README')
    self.assertTrue(result)

  def testCheckHasBranch(self):
    """Tests the CheckHasBranch function."""
    git_helper = TestGitHelper(self._GIT_REPO_URL)

    result = git_helper.CheckHasBranch(u'master')
    self.assertTrue(result)

    result = git_helper.CheckHasBranch(u'feature')
    self.assertTrue(result)

    result = git_helper.CheckHasBranch(u'bogus')
    self.assertFalse(result)

    git_helper = ErrorGitHelper(self._GIT_REPO_URL)

    result = git_helper.CheckHasBranch(u'master')
    self.assertFalse(result)

  def testCheckHasProjectOrigin(self):
    """Tests the CheckHasProjectOrigin function."""
    git_helper = review.GitHelper(self._GIT_REPO_URL)

    # Only test if the method completes without errors.
    git_helper.CheckHasProjectOrigin()

  def testCheckHasProjectUpstream(self):
    """Tests the CheckHasProjectUpstream function."""
    git_helper = review.GitHelper(self._GIT_REPO_URL)

    # Only test if the method completes without errors.
    git_helper.CheckHasProjectUpstream()

  def testCheckHasUncommittedChanges(self):
    """Tests the CheckHasUncommittedChanges function."""
    git_helper = review.GitHelper(self._GIT_REPO_URL)

    # Only test if the method completes without errors.
    git_helper.CheckHasUncommittedChanges()

  def testCheckSynchronizedWithUpstream(self):
    """Tests the CheckSynchronizedWithUpstream function."""
    git_helper = review.GitHelper(self._GIT_REPO_URL)

    # Only test if the method completes without errors.
    git_helper.CheckSynchronizedWithUpstream()

  # TODO: add CommitToOriginInNameOf test.
  # TODO: add DropUncommittedChanges test.

  def testGetActiveBranch(self):
    """Tests the GetActiveBranch function."""
    git_helper = review.GitHelper(self._GIT_REPO_URL)

    active_branch = git_helper.GetActiveBranch()
    self.assertIsNotNone(active_branch)

  def testGetChangedFiles(self):
    """Tests the GetChangedFiles function."""
    git_helper = review.GitHelper(self._GIT_REPO_URL)

    # Only test if the method completes without errors.
    git_helper.GetChangedFiles(u'origin/master')

  def testGetChangedPythonFiles(self):
    """Tests the GetChangedPythonFiles function."""
    git_helper = review.GitHelper(self._GIT_REPO_URL)

    # Only test if the method completes without errors.
    git_helper.GetChangedPythonFiles(u'origin/master')

  def testGetEmailAddress(self):
    """Tests the GetEmailAddress function."""
    if os.environ.get(u'TRAVIS_OS_NAME', u''):
      git_helper = TestGitHelper(self._GIT_REPO_URL)
    else:
      git_helper = review.GitHelper(self._GIT_REPO_URL)

    email_address = git_helper.GetEmailAddress()
    self.assertIsNotNone(email_address)

  def testGetLastCommitMessage(self):
    """Tests the GetLastCommitMessage function."""
    if os.environ.get(u'TRAVIS_OS_NAME', u''):
      git_helper = TestGitHelper(self._GIT_REPO_URL)
    else:
      git_helper = review.GitHelper(self._GIT_REPO_URL)

    last_commit_message = git_helper.GetLastCommitMessage()
    self.assertIsNotNone(last_commit_message)

  def testGetRemoteOrigin(self):
    """Tests the GetRemoteOrigin function."""
    git_helper = TestGitHelper(self._GIT_REPO_URL)

    expected_remote_origin = u'https://github.com/username/l2tdevtools.git'
    remote_origin = git_helper.GetRemoteOrigin()
    self.assertEqual(remote_origin, expected_remote_origin)

  def testPullFromFork(self):
    """Tests the PullFromFork function."""
    git_helper = TestGitHelper(self._GIT_REPO_URL)

    result = git_helper.PullFromFork(
        u'https://github.com/username/l2tdevtools.git', u'feature')
    self.assertTrue(result)

  def testPushToOrigin(self):
    """Tests the PushToOrigin function."""
    git_helper = TestGitHelper(self._GIT_REPO_URL)

    result = git_helper.PushToOrigin(u'feature')
    self.assertTrue(result)

    result = git_helper.PushToOrigin(u'feature', force=True)
    self.assertTrue(result)

  def testRemoveFeatureBranch(self):
    """Tests the RemoveFeatureBranch function."""
    git_helper = TestGitHelper(self._GIT_REPO_URL)

    git_helper.RemoveFeatureBranch(u'feature')
    git_helper.RemoveFeatureBranch(u'master')

    # TODO: add return value.

  def testSynchronizeWithOrigin(self):
    """Tests the SynchronizeWithOrigin function."""
    git_helper = TestGitHelper(self._GIT_REPO_URL)

    result = git_helper.SynchronizeWithOrigin()
    self.assertTrue(result)

    git_helper = ErrorGitHelper(self._GIT_REPO_URL)

    result = git_helper.SynchronizeWithOrigin()
    self.assertFalse(result)

  def testSynchronizeWithUpstream(self):
    """Tests the SynchronizeWithUpstream function."""
    git_helper = TestGitHelper(self._GIT_REPO_URL)

    result = git_helper.SynchronizeWithUpstream()
    self.assertTrue(result)

    git_helper = ErrorGitHelper(self._GIT_REPO_URL)

    result = git_helper.SynchronizeWithUpstream()
    self.assertFalse(result)

  def testSwitchToMasterBranch(self):
    """Tests the SwitchToMasterBranch function."""
    git_helper = TestGitHelper(self._GIT_REPO_URL)

    result = git_helper.SwitchToMasterBranch()
    self.assertTrue(result)


class GitHubHelperTest(unittest.TestCase):
  """Tests for the github helper class."""

  # TODO: add CreatePullRequest test.
  # TODO: add GetForkGitRepoUrl test.

  @unittest.skipIf(
      os.environ.get(u'TRAVIS_OS_NAME', u''), 'Travis-CI not supported')
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

    # TODO: determine why this test fails on Travis-CI osx.


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

  # TODO: add version_file_path test.
  # TODO: add _GetProjectName test.
  # TODO: add _ReadFileContents test.
  # TODO: add GetVersion test.
  # TODO: add UpdateDpkgChangelogFile test.
  # TODO: add UpdateAuthorsFile test.
  # TODO: add UpdateVersionFile test.


@unittest.skipIf(
    os.environ.get(u'TRAVIS_OS_NAME', u''), 'Travis-CI not supported')
class PylintHelperTest(unittest.TestCase):
  """Tests for the pylint helper class."""

  def setUp(self):
    """Sets up a test case."""
    self._pylint_helper = review.PylintHelper()

  def testCheckFiles(self):
    """Tests the CheckFiles function."""
    test_file = os.path.join(u'test_data', u'linter_pass.py')
    result = self._pylint_helper.CheckFiles([test_file])
    self.assertTrue(result)

    test_file = os.path.join(u'test_data', u'linter_fail.py')
    result = self._pylint_helper.CheckFiles([test_file])
    self.assertFalse(result)

    # TODO: capture output and compare.

  def testCheckUpToDateVersion(self):
    """Tests the CheckUpToDateVersion function."""
    result = self._pylint_helper.CheckUpToDateVersion()
    self.assertTrue(result)


class ReadTheDocsHelperTest(unittest.TestCase):
  """Tests for the readthedocs helper functions."""

  # TODO: add TriggerBuild test.


class SphinxAPIDocHelperTest(unittest.TestCase):
  """Tests for the sphinx-apidoc helper class."""

  def setUp(self):
    """Sets up a test case."""
    self._sphinxapidoc_helper = review.SphinxAPIDocHelper(u'plaso')

  # TODO: the version check fails for sphinx-apidoc 1.2.2 on Unbuntu 14.04.
  @unittest.expectedFailure
  def testCheckUpToDateVersion(self):
    """Tests the CheckUpToDateVersion function."""
    self.assertTrue(self._sphinxapidoc_helper.CheckUpToDateVersion())

  # TODO: add UpdateAPIDocs test.


class NetRCFileTest(unittest.TestCase):
  """Tests for the .netrc file class."""

  # TODO: add _GetGitHubValues test.

  def testGetGitHubAccessToken(self):
    """Tests the GetGitHubAccessToken function."""
    # Only test if the method completes without errors.
    netrc_file = review.NetRCFile()
    netrc_file.GetGitHubAccessToken()

  # TODO: add GetGitHubUsername test.


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


# TODO: add ReviewHelper test case.


if __name__ == '__main__':
  unittest.main()
