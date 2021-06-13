# -*- coding: utf-8 -*-
"""Helper for conducting code reviews."""


import os
import re
import subprocess
import sys

from l2tdevtools.helpers import project
from l2tdevtools.lib import errors
from l2tdevtools.lib import netrcfile
from l2tdevtools.review_helpers import git
from l2tdevtools.review_helpers import github
from l2tdevtools.review_helpers import pylint
from l2tdevtools.review_helpers import yapf


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
      all_files=False, no_browser=False, no_confirm=False,
      no_edit=False):
    """Initializes a review helper.

    Args:
      command (str): user provided command, for example "create", "lint".
      project_path (str): path to the project being reviewed.
      github_origin (str): GitHub origin.
      feature_branch (str): feature branch.
      all_files (Optional[bool]): True if the command should apply to all
          files. Currently this only affects the lint command.
      no_browser (Optional[bool]): True if the functionality to use the
          webbrowser to get the OAuth token should be disabled.
      no_confirm (Optional[bool]): True if the defaults should be applied
          without confirmation.
      no_edit (Optional[bool]): True if maintainers should not be allowed to
          edit the pull request.
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
    self._no_browser = no_browser
    self._no_confirm = no_confirm
    self._no_edit = no_edit
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
          self._git_helper.SwitchToMasterBranch()
          self._active_branch = 'main'

    return True

  def CheckRemoteGitState(self):
    """Checks the state of the remote git repository.

    Returns:
      bool: True if the state of the remote git repository is sane.
    """
    if self._github_organization in ('ForensicArtifacts', 'log2timeline'):
      if self._command == 'close':
        if not self._git_helper.SynchronizeWithUpstream():
          print((
              '{0:s} aborted - unable to synchronize with '
              'upstream/main.').format(self._command.title()))
          return False

      elif self._command in ('create-pr', 'create_pr'):
        if not self._git_helper.CheckSynchronizedWithUpstream():
          if not self._git_helper.SynchronizeWithUpstream():
            print((
                '{0:s} aborted - unable to synchronize with '
                'upstream/main.').format(self._command.title()))
            return False

          force_push = True
        else:
          force_push = False

        if not self._git_helper.PushToOrigin(
            self._active_branch, force=force_push):
          print((
              '{0:s} aborted - unable to push updates to origin/{1:s}.').format(
                  self._command.title(), self._active_branch))
          return False

      elif self._command in ('lint', 'lint-test', 'lint_test'):
        self._git_helper.CheckSynchronizedWithUpstream()

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

    return True

  def CreatePullRequest(self):
    """Creates a GitHub pull request.

    Returns:
      bool: True if the pull request was created, assigned and requested to
          review successfully.
    """
    git_origin = self._git_helper.GetRemoteOrigin()
    if not git_origin.startswith('https://github.com/'):
      print('{0:s} aborted - unsupported git remote origin: {1:s}'.format(
          self._command.title(), git_origin))
      print('Make sure the git remote origin is hosted on github.com')
      return False

    git_origin, _, _ = git_origin[len('https://github.com/'):].rpartition('/')

    netrc_file = netrcfile.NetRCFile()
    github_access_token = netrc_file.GetGitHubAccessToken()
    if not github_access_token:
      print('{0:s} aborted - unable to determine github access token.'.format(
          self._command.title()))
      print('Make sure .netrc is configured with a github access token.')
      return False

    last_commit_message = self._git_helper.GetLastCommitMessage()
    print('Automatic generated description of code review:')
    print(last_commit_message)
    print('')

    if self._no_confirm:
      user_input = None
    else:
      print('Enter a description for the code review or hit enter to use the')
      print('automatic generated one:')
      user_input = sys.stdin.readline()
      user_input = user_input.strip()

    if not user_input:
      title = last_commit_message
      body = last_commit_message
    else:
      title = user_input
      body = user_input

    create_github_origin = '{0:s}:{1:s}'.format(git_origin, self._active_branch)
    try:
      pull_request_number = self._github_helper.CreatePullRequest(
          github_access_token, create_github_origin, title, body,
          no_edit=self._no_edit)

    except errors.ConnectivityError as exception:
      print('Unable to create pull request with error: {0!s}.'.format(
          exception))
      return False

    try:
      github_username = self._github_helper.GetUsername(github_access_token)

    except errors.ConnectivityError:
      print('Unable to determine GitHub username.')
      return False

    result = True

    # When a pull request is created try to assign a reviewer.
    reviewer = project.ProjectHelper.GetReviewer(
        self._project_name, github_username)

    try:
      self._github_helper.CreatePullRequestReview(
          pull_request_number, github_access_token, [reviewer])

    except errors.ConnectivityError:
      print('Unable to request review of pull request.')
      result = False

    try:
      self._github_helper.AssignPullRequest(
          pull_request_number, github_access_token, [reviewer])

    except errors.ConnectivityError:
      print('Unable to assign pull request.')
      result = False

    pull_request_url = (
        'https://github.com/{0:s}/{1:s}/pull/{2:d}').format(
            self._github_organization, self._project_name, pull_request_number)
    print('Pull request created: {0:s}'.format(pull_request_url))
    print('Review assigned to: {0:s}'.format(reviewer))
    print('')

    return result

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

  def CheckStyle(self):
    """Checks the code style of a change.

    Returns:
      bool: True if the code style check was successful or no style was defined.
    """
    yapf_helper = yapf.YapfHelper()
    configuration = yapf_helper.GetStyleConfig(self._project_path)
    if not configuration:
      return True

    if self._command not in self._CODE_INSPECTION_COMMANDS:
      return True

    if not yapf_helper.CheckUpToDateVersion():
      message = '{0:s} aborted - yapf version {1:s} or later required.'.format(
          self._command.title(), pylint.PylintHelper.MINIMUM_VERSION)
      print(message)
      return False

    if self._all_files:
      diffbase = None
    else:
      diffbase = 'origin/main'

    changed_python_files = self._git_helper.GetChangedPythonFiles(
        diffbase=diffbase)

    if not yapf_helper.CheckFiles(changed_python_files, configuration):
      message = '{0:s} aborted - unable to pass style inspection.'.format(
          self._command.title())
      print(message)

      return False

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

  def PullChangesFromFork(self):
    """Pulls changes from a feature branch on a fork.

    Returns:
      bool: True if the pull was successful.
    """
    fork_git_repo_url = self._github_helper.GetForkGitRepoUrl(
        self._fork_username)

    if not self._git_helper.PullFromFork(
        fork_git_repo_url, self._fork_feature_branch):
      print('{0:s} aborted - unable to pull changes from fork.'.format(
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
