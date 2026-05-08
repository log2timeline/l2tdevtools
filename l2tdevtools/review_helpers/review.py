"""Helper for conducting code reviews."""


import os
import re
import subprocess
import sys

from l2tdevtools.helpers import project
from l2tdevtools.review_helpers import git
from l2tdevtools.review_helpers import github
from l2tdevtools.review_helpers import pylint


class ReviewHelper:
  """Helper for conducting code reviews."""

  _SUPPORTED_PROJECTS_PATTERN = '|'.join(
      project.ProjectHelper.SUPPORTED_PROJECTS)
  _PROJECT_NAME_PREFIX_REGEX = re.compile(
      rf'\[({_SUPPORTED_PROJECTS_PATTERN})\] ')

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
    super().__init__()
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
          command_title = self._command.title()
          print(f'{command_title:s} aborted - missing project upstream.')
          print(f'Run: git remote add upstream {self._git_repo_url:s}')
          return False

    if self._command not in (
        'lint', 'lint-test', 'lint_test', 'test', 'update-version',
        'update_version'):
      if self._git_helper.CheckHasUncommittedChanges():
        command_title = self._command.title()
        print(f'{command_title:s} aborted - detected uncommitted changes.')
        print('Run: git commit')
        return False

    if self._github_organization in ('ForensicArtifacts', 'log2timeline'):
      self._active_branch = self._git_helper.GetActiveBranch()
      if self._command in ('create-pr', 'create_pr'):
        if self._active_branch == 'main':
          command_title = self._command.title()
          print(f'{command_title:s} aborted - active branch is main.')
          return False

      elif self._command == 'close':
        if self._feature_branch == 'main':
          command_title = self._command.title()
          print(f'{command_title:s} aborted - feature branch cannot be main.')
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
      print(f'No such feature branch: {self._feature_branch:s}')
    else:
      self._git_helper.RemoveFeatureBranch(self._feature_branch)

    if not self._git_helper.SynchronizeWithUpstream():
      command_title = self._command.title()
      print(
          f'{command_title:s} aborted - unable to synchronize with '
          f'upstream/main.')

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
      command_title = self._command.title()
      print(f'{command_title:s} aborted - unable to determine project name.')
      return False

    project_definition = self._project_helper.ReadDefinitionFile()

    self._github_organization = None
    if project_definition.homepage_url.startswith('https://github.com/'):
      self._github_organization = project_definition.homepage_url[
          len('https://github.com/'):]

      self._github_organization, _, _ = self._github_organization.partition('/')

    if not self._github_organization:
      command_title = self._command.title()
      print(
          f'{command_title:s} aborted - unable to determine GitHub '
          f'organization.')
      return False

    self._git_repo_url = (
        f'https://github.com/'
        f'{self._github_organization:s}/{self._project_name:s}.git')

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
      command_title = self._command.title()
      min_version = pylint.PylintHelper.MINIMUM_VERSION
      print(
          f'{command_title:s} aborted - pylint version {min_version:s} '
          f'or later required.')
      return False

    if self._all_files:
      diffbase = None
    else:
      diffbase = 'main'

    changed_python_files = self._git_helper.GetChangedPythonFiles(
        diffbase=diffbase)

    pylint_configuration = pylint_helper.GetRCFile(self._project_path)
    if not pylint_helper.CheckFiles(changed_python_files, pylint_configuration):
      command_title = self._command.title()
      print(f'{command_title:s} aborted - unable to pass linter.')

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
    command = f'{sys.executable:s} run_tests.py'
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      command_title = self._command.title()
      print(f'{command_title:s} aborted - unable to pass review.')

      return False

    return True
