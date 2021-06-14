# -*- coding: utf-8 -*-
"""Helper for conducting code reviews."""


import os
import re
import subprocess
import sys

from l2tdevtools.helpers import project
from l2tdevtools.review_helpers import git
from l2tdevtools.review_helpers import github
from l2tdevtools.review_helpers import pylint


class ReviewHelper(object):
  """Helper for conducting code reviews."""

  _PROJECT_NAME_PREFIX_REGEX = re.compile(
      r'\[({0:s})\] '.format(
          '|'.join(project.ProjectHelper.SUPPORTED_PROJECTS)))

  # Commands that trigger inspection (pylint, yapf) of changed files.
  _CODE_INSPECTION_COMMANDS = frozenset([
      'create-pr', 'create_pr', 'lint', 'lint-test', 'lint_test'])

  def __init__(
      self, command, project_path, github_origin, feature_branch,
      all_files=False):
    """Initializes a review helper.

    Args:
      command (str): user provided command, for example "create", "lint".
      project_path (str): path to the project being reviewed.
      github_origin (str): GitHub origin.
      feature_branch (str): feature branch.
      all_files (Optional[bool]): True if the command should apply to all
          files. Currently this only affects the lint command.
    """
    super(ReviewHelper, self).__init__()
    self._active_branch = None
    self._all_files = all_files
    self._command = command
    self._feature_branch = feature_branch
    self._git_helper = None
    self._git_repo_url = None
    self._github_helper = None
    self._github_organization = None
    self._github_origin = github_origin
    self._fork_feature_branch = None
    self._fork_username = None
    self._maintainer = None
    self._project_helper = None
    self._project_name = None
    self._project_path = project_path

    if self._github_origin:
      self._fork_username, _, self._fork_feature_branch = (
          self._github_origin.partition(':'))

  def CheckLocalGitState(self):
    """Checks the state of the local git repository.

    Returns:
      bool: True if the state of the local git repository is sane.
    """
    if self._github_organization in ('ForensicArtifacts', 'log2timeline'):
      if self._command in (
          'close', 'create-pr', 'create_pr', 'lint', 'lint-test', 'lint_test'):
        if not self._git_helper.CheckHasProjectUpstream():
          print('{0:s} aborted - missing project upstream.'.format(
              self._command.title()))
          print('Run: git remote add upstream {0:s}'.format(self._git_repo_url))
          return False

    if self._command not in (
        'lint', 'lint-test', 'lint_test', 'test', 'update-version',
        'update_version'):
      if self._git_helper.CheckHasUncommittedChanges():
        print('{0:s} aborted - detected uncommitted changes.'.format(
            self._command.title()))
        print('Run: git commit')
        return False

    if self._github_organization in ('ForensicArtifacts', 'log2timeline'):
      self._active_branch = self._git_helper.GetActiveBranch()
      if self._command in ('create-pr', 'create_pr'):
        if self._active_branch == 'main':
          print('{0:s} aborted - active branch is main.'.format(
              self._command.title()))
          return False

      elif self._command == 'close':
        if self._feature_branch == 'main':
          print('{0:s} aborted - feature branch cannot be main.'.format(
              self._command.title()))
          return False

        if self._active_branch != 'main':
          self._git_helper.SwitchToMainBranch()
          self._active_branch = 'main'

    return True

  def Close(self):
    """Closes a review.

    Returns:
      bool: True if the close was successful.
    """
    if not self._git_helper.CheckHasBranch(self._feature_branch):
      print('No such feature branch: {0:s}'.format(self._feature_branch))
    else:
      self._git_helper.RemoveFeatureBranch(self._feature_branch)

    if not self._git_helper.SynchronizeWithUpstream():
      print((
          '{0:s} aborted - unable to synchronize with '
          'upstream/main.').format(self._command.title()))

    return True

  def InitializeHelpers(self):
    """Initializes the helpers.

    Returns:
      bool: True if the helper initialization was successful.
    """
    project_path = os.path.abspath(self._project_path)

    self._project_helper = project.ProjectHelper(project_path)

    self._project_name = self._project_helper.project_name
    if not self._project_name:
      print('{0:s} aborted - unable to determine project name.'.format(
          self._command.title()))
      return False

    project_definition = self._project_helper.ReadDefinitionFile()

    self._github_organization = None
    if project_definition.homepage_url.startswith('https://github.com/'):
      self._github_organization = project_definition.homepage_url[
          len('https://github.com/'):]

      self._github_organization, _, _ = self._github_organization.partition('/')

    if not self._github_organization:
      print('{0:s} aborted - unable to determine GitHub organization.'.format(
          self._command.title()))
      return False

    self._git_repo_url = 'https://github.com/{0:s}/{1:s}.git'.format(
        self._github_organization, self._project_name)

    self._git_helper = git.GitHelper(self._git_repo_url)

    self._github_helper = github.GitHubHelper(
        self._github_organization, self._project_name)

    return True

  def Lint(self):
    """Lints a review.

    Returns:
      bool: True if linting was successful.
    """
    if self._project_name == 'l2tdocs':
      return True

    if self._command not in self._CODE_INSPECTION_COMMANDS:
      return True

    pylint_helper = pylint.PylintHelper()
    if not pylint_helper.CheckUpToDateVersion():
      print('{0:s} aborted - pylint version {1:s} or later required.'.format(
          self._command.title(), pylint.PylintHelper.MINIMUM_VERSION))
      return False

    if self._all_files:
      diffbase = None
    else:
      diffbase = 'origin/main'

    changed_python_files = self._git_helper.GetChangedPythonFiles(
        diffbase=diffbase)

    pylint_configuration = pylint_helper.GetRCFile(self._project_path)
    if not pylint_helper.CheckFiles(changed_python_files, pylint_configuration):
      print('{0:s} aborted - unable to pass linter.'.format(
          self._command.title()))

      return False

    return True

  def Test(self):
    """Tests a review.

    Returns:
      bool: True if the review were successful.
    """
    if self._project_name == 'l2tdocs':
      return True

    if self._command not in (
        'create-pr', 'create_pr', 'lint-test', 'lint_test', 'test'):
      return True

    # TODO: determine why this alters the behavior of argparse.
    # Currently affects this script being used in plaso.
    command = '{0:s} run_tests.py'.format(sys.executable)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      print('{0:s} aborted - unable to pass review.'.format(
          self._command.title()))

      return False

    return True
