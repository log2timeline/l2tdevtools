# -*- coding: utf-8 -*-
"""Helper for conducting code reviews."""

from __future__ import print_function
from __future__ import unicode_literals

import os
import re
import subprocess
import sys

from l2tdevtools.review_helpers import github
from l2tdevtools.review_helpers import projects
from l2tdevtools.review_helpers import pylint
from l2tdevtools.review_helpers import upload
from l2tdevtools.review_helpers import yapf

from l2tdevtools.review_helpers import git
from l2tdevtools.lib import netrcfile
from l2tdevtools.lib import reviewfile


class ReviewHelper(object):
  """Helper for conducting code reviews."""

  _PROJECT_NAME_PREFIX_REGEX = re.compile(
      r'\[({0:s})\] '.format(
          '|'.join(projects.ProjectsHelper.SUPPORTED_PROJECTS)))

  # Commands that trigger inspection (pylint, yapf) of changed files.
  _CODE_INSPECTION_COMMANDS = frozenset(
      ['create', 'merge', 'lint', 'lint-test', 'lint_test', 'update'])

  def __init__(
      self, command, project_path, github_origin, feature_branch, diffbase,
      all_files=False, no_browser=False, no_confirm=False):  # yapf: disable
    """Initializes a review helper.

    Args:
      command (str): user provided command, for example "create", "lint".
      project_path (str): path to the project being reviewed.
      github_origin (str): github origin.
      feature_branch (str): feature branch.
      diffbase (str): diffbase.
      all_files (Optional[bool]): True if the command should apply to all
          files. Currently this only affects the lint command.
      no_browser (Optional[bool]): True if the functionality to use the
          webbrowser to get the OAuth token should be disabled.
      no_confirm (Optional[bool]): True if the defaults should be applied
          without confirmation.
    """
    super(ReviewHelper, self).__init__()
    self._active_branch = None
    self._all_files = all_files
    self._codereview_helper = None
    self._codereview_issue_number = None
    self._command = command
    self._diffbase = diffbase
    self._feature_branch = feature_branch
    self._git_helper = None
    self._git_repo_url = None
    self._github_helper = None
    self._github_origin = github_origin
    self._fork_feature_branch = None
    self._fork_username = None
    self._merge_author = None
    self._merge_description = None
    self._no_browser = no_browser
    self._no_confirm = no_confirm
    self._projects_helper = None
    self._project_name = None
    self._project_path = project_path

    if self._github_origin:
      self._fork_username, _, self._fork_feature_branch = (
          self._github_origin.partition(':'))

  # yapf: disable
  def CheckLocalGitState(self):
    """Checks the state of the local git repository.

    Returns:
      bool: True if the state of the local git repository is sane.
    """
    if self._command in (
        'close', 'create', 'create-pr', 'create_pr', 'lint', 'lint-test',
        'lint_test', 'update'):
      if not self._git_helper.CheckHasProjectUpstream():
        print('{0:s} aborted - missing project upstream.'.format(
            self._command.title()))
        print('Run: git remote add upstream {0:s}'.format(self._git_repo_url))
        return False

    elif self._command == 'merge':
      if not self._git_helper.CheckHasProjectOrigin():
        print('{0:s} aborted - missing project origin.'.format(
            self._command.title()))
        return False

    if self._command not in (
        'lint', 'lint-test', 'lint_test', 'test', 'update-version',
        'update_version'):
      if self._git_helper.CheckHasUncommittedChanges():
        print('{0:s} aborted - detected uncommitted changes.'.format(
            self._command.title()))
        print('Run: git commit')
        return False

    self._active_branch = self._git_helper.GetActiveBranch()
    if self._command in ('create', 'create-pr', 'create_pr', 'update'):
      if self._active_branch == 'master':
        print('{0:s} aborted - active branch is master.'.format(
            self._command.title()))
        return False

    elif self._command == 'close':
      if self._feature_branch == 'master':
        print('{0:s} aborted - feature branch cannot be master.'.format(
            self._command.title()))
        return False

      if self._active_branch != 'master':
        self._git_helper.SwitchToMasterBranch()
        self._active_branch = 'master'

    return True
  # yapf: enable

  # yapf: disable
  def CheckRemoteGitState(self):
    """Checks the state of the remote git repository.

    Returns:
      bool: True if the state of the remote git repository is sane.
    """
    if self._command == 'close':
      if not self._git_helper.SynchronizeWithUpstream():
        print((
            '{0:s} aborted - unable to synchronize with '
            'upstream/master.').format(self._command.title()))
        return False

    elif self._command in ('create', 'create-pr', 'create_pr', 'update'):
      if not self._git_helper.CheckSynchronizedWithUpstream():
        if not self._git_helper.SynchronizeWithUpstream():
          print((
              '{0:s} aborted - unable to synchronize with '
              'upstream/master.').format(self._command.title()))
          return False

        force_push = True
      else:
        force_push = False

      if not self._git_helper.PushToOrigin(
          self._active_branch, force=force_push):
        print('{0:s} aborted - unable to push updates to origin/{1:s}.'.format(
            self._command.title(), self._active_branch))
        return False

    elif self._command in ('lint', 'lint-test', 'lint_test'):
      self._git_helper.CheckSynchronizedWithUpstream()

    elif self._command == 'merge':
      if not self._git_helper.SynchronizeWithOrigin():
        print(
            ('{0:s} aborted - unable to synchronize with '
             'origin/master.').format(self._command.title()))
        return False

    return True
  # yapf: enable

  def Close(self):
    """Closes a review.

    Returns:
      bool: True if the close was successful.
    """
    if not self._git_helper.CheckHasBranch(self._feature_branch):
      print('No such feature branch: {0:s}'.format(self._feature_branch))
    else:
      self._git_helper.RemoveFeatureBranch(self._feature_branch)

    review_file = reviewfile.ReviewFile(self._feature_branch)
    if not review_file.Exists():
      print('Review file missing for branch: {0:s}'.format(
          self._feature_branch))  # yapf: disable

    else:
      codereview_issue_number = review_file.GetCodeReviewIssueNumber()

      review_file.Remove()

      if codereview_issue_number:
        if not self._codereview_helper.CloseIssue(codereview_issue_number):
          print('Unable to close code review: {0!s}'.format(
              codereview_issue_number))  # yapf: disable
          print(
              ('Close it manually on: https://codereview.appspot.com/'
               '{0!s}').format(codereview_issue_number))

    return True

  def Create(self):
    """Creates a review.

    Returns:
      bool: True if the create was successful.
    """
    # yapf: disable
    review_file = reviewfile.ReviewFile(self._active_branch)
    if review_file.Exists():
      print('Review file already exists for branch: {0:s}'.format(
          self._active_branch))
      return False

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
      description = last_commit_message
    else:
      description = user_input

    # Prefix the description with the project name for code review to make it
    # easier to distinguish between projects.
    code_review_description = '[{0:s}] {1:s}'.format(
        self._project_name, description)

    codereview_issue_number = self._codereview_helper.CreateIssue(
        self._project_name, self._diffbase, code_review_description)
    if not codereview_issue_number:
      print('{0:s} aborted - unable to create codereview issue.'.format(
          self._command.title()))
      return False

    if not os.path.isdir('.review'):
      os.mkdir('.review')

    review_file.Create(codereview_issue_number)

    title = '{0!s}: {1:s}'.format(codereview_issue_number, description)
    body = (
        '[Code review: {0!s}: {1:s}]'
        '(https://codereview.appspot.com/{0!s}/)').format(
            codereview_issue_number, description)

    create_github_origin = '{0:s}:{1:s}'.format(git_origin, self._active_branch)
    if not self._github_helper.CreatePullRequest(
        github_access_token, create_github_origin, title, body):
      print('Unable to create pull request.')

    # yapf: enable
    return True

  def CreatePullRequest(self):
    """Creates a github pull request.

    Returns:
      bool: True if the create was successful.
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
    if not self._github_helper.CreatePullRequest(
        github_access_token, create_github_origin, title, body):
      print('Unable to create pull request.')

    return True

  def InitializeHelpers(self):
    """Initializes the helper.

    Returns:
      bool: True if the helper initialization was successful.
    """
    project_path = os.path.abspath(self._project_path)

    self._projects_helper = projects.ProjectsHelper(project_path)

    self._project_name = self._projects_helper.project_name
    if not self._project_name:
      print('{0:s} aborted - unable to determine project name.'.format(
          self._command.title()))  # yapf: disable
      return False

    self._git_repo_url = b'https://github.com/log2timeline/{0:s}.git'.format(
        self._project_name)

    self._git_helper = git.GitHelper(self._git_repo_url)

    self._github_helper = github.GitHubHelper(
        'log2timeline', self._project_name)

    if self._command in ('close', 'create', 'merge', 'update'):
      email_address = self._git_helper.GetEmailAddress()
      self._codereview_helper = upload.UploadHelper(
          email_address, no_browser=self._no_browser)

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
    elif self._command == 'merge':
      diffbase = 'origin/master'
    else:
      diffbase = self._diffbase

    changed_python_files = self._git_helper.GetChangedPythonFiles(
        diffbase=diffbase)

    if not yapf_helper.CheckFiles(changed_python_files, configuration):
      message = '{0:s} aborted - unable to pass style inspection.'.format(
          self._command.title())
      print(message)

      if self._command == 'merge':
        self._git_helper.DropUncommittedChanges()
      return False

    return True

  # yapf: disable
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
    elif self._command == 'merge':
      diffbase = 'origin/master'
    else:
      diffbase = self._diffbase

    changed_python_files = self._git_helper.GetChangedPythonFiles(
        diffbase=diffbase)

    pylint_configuration = pylint_helper.GetRCFile(self._project_path)
    if not pylint_helper.CheckFiles(changed_python_files, pylint_configuration):
      print('{0:s} aborted - unable to pass linter.'.format(
          self._command.title()))

      if self._command == 'merge':
        self._git_helper.DropUncommittedChanges()
      return False

    return True
  # yapf: enable

  def Merge(self, codereview_issue_number):
    """Merges a review.

    Args:
      codereview_issue_number (int|str): codereview issue number.

    Returns:
      bool: True if the merge was successful.
    """
    if not self._projects_helper.UpdateVersionFile():
      print('Unable to update version file.')
      self._git_helper.DropUncommittedChanges()
      return False

    if not self._projects_helper.UpdateDpkgChangelogFile():
      print('Unable to update dpkg changelog file.')
      self._git_helper.DropUncommittedChanges()
      return False

    if not self._git_helper.CommitToOriginInNameOf(
        codereview_issue_number, self._merge_author, self._merge_description):
      print('Unable to commit changes.')
      self._git_helper.DropUncommittedChanges()
      return False

    commit_message = (
        'Changes have been merged with master branch. '
        'To close the review and clean up the feature branch you can run: '
        'review.py close {0:s}').format(self._fork_feature_branch)
    self._codereview_helper.AddMergeMessage(
        codereview_issue_number, commit_message)

    return True

  def Open(self, codereview_issue_number):
    """Opens a review.

    Args:
      codereview_issue_number (int|str): codereview issue number.

    Returns:
      bool: True if the open was successful.
    """
    # TODO: implement.
    # * check if feature branch exists
    # * check if review file exists
    # * check if issue number corresponds to branch by checking PR?
    # * create feature branch and pull changes from origin
    # * create review file
    _ = codereview_issue_number

    return False

  def PrepareMerge(self, codereview_issue_number):
    """Prepares a merge.

    Args:
      codereview_issue_number (int|str): codereview issue number.

    Returns:
      bool: True if the prepare were successful.
    """
    codereview_information = self._codereview_helper.QueryIssue(
        codereview_issue_number)
    if not codereview_information:
      print((
          '{0:s} aborted - unable to retrieve code review: {1!s} '
          'information.').format(
              self._command.title(), codereview_issue_number))
      return False

    self._merge_description = codereview_information.get('subject', None)
    if not self._merge_description:
      print((
          '{0:s} aborted - unable to determine description of code review: '
          '{1!s}.').format(self._command.title(), codereview_issue_number))
      return False

    # When merging remove the project name ("[project]") prefix from
    # the code review description.
    self._merge_description = self._PROJECT_NAME_PREFIX_REGEX.sub(
        '', self._merge_description)

    merge_email_address = codereview_information.get('owner_email', None)
    if not merge_email_address:
      print((
          '{0:s} aborted - unable to determine email address of owner of '
          'code review: {1!s}.').format(
              self._command.title(), codereview_issue_number))
      return False

    github_user_information = self._github_helper.QueryUser(self._fork_username)
    if not github_user_information:
      print((
          '{0:s} aborted - unable to retrieve github user: {1:s} '
          'information.').format(self._command.title(), self._fork_username))
      return False

    merge_fullname = github_user_information.get('name', None)
    if not merge_fullname:
      merge_fullname = codereview_information.get('owner', None)
    if not merge_fullname:
      merge_fullname = github_user_information.get('company', None)
    if not merge_fullname:
      print((
          '{0:s} aborted - unable to determine full name.').format(
              self._command.title()))  # yapf: disable
      return False

    self._merge_author = '{0:s} <{1:s}>'.format(
        merge_fullname, merge_email_address)

    return True

  def PrepareUpdate(self):
    """Prepares to update a review.

    Returns:
      bool: True if the preparations were successful.
    """
    review_file = reviewfile.ReviewFile(self._active_branch)
    if not review_file.Exists():
      print('Review file missing for branch: {0:s}'.format(
          self._active_branch))  # yapf: disable
      return False

    self._codereview_issue_number = review_file.GetCodeReviewIssueNumber()

    return True

  def PullChangesFromFork(self):
    """Pulls changes from a feature branch on a fork.

    Returns:
      bool: True if the pull was successful.
    """
    fork_git_repo_url = self._github_helper.GetForkGitRepoUrl(
        self._fork_username)

    # yapf: disable
    if not self._git_helper.PullFromFork(
        fork_git_repo_url, self._fork_feature_branch):
      print('{0:s} aborted - unable to pull changes from fork.'.format(
          self._command.title()))
      return False
    # yapf: enable

    return True

  # yapf: disable
  def Test(self):
    """Tests a review.

    Returns:
      bool: True if the review were successful.
    """
    if self._project_name == 'l2tdocs':
      return True

    if self._command not in (
        'create', 'create-pr', 'create_pr', 'lint-test', 'lint_test', 'merge',
        'test', 'update'):
      return True

    # TODO: determine why this alters the behavior of argparse.
    # Currently affects this script being used in plaso.
    command = '{0:s} run_tests.py'.format(sys.executable)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      print('{0:s} aborted - unable to pass review.'.format(
          self._command.title()))

      if self._command == 'merge':
        self._git_helper.DropUncommittedChanges()
      return False

    return True

  # yapf: enable

  def Update(self):
    """Updates a review.

    Returns:
      bool: True if the update was successful.
    """
    last_commit_message = self._git_helper.GetLastCommitMessage()
    print('Automatic generated description of the update:')
    print(last_commit_message)
    print('')

    if self._no_confirm:
      user_input = None
    else:
      print('Enter a description for the update or hit enter to use the')
      print('automatic generated one:')
      user_input = sys.stdin.readline()
      user_input = user_input.strip()

    if not user_input:
      description = last_commit_message
    else:
      description = user_input

    # yapf: disable
    if not self._codereview_helper.UpdateIssue(
        self._codereview_issue_number, self._diffbase, description):
      print('Unable to update code review: {0!s}'.format(
          self._codereview_issue_number))
      return False

    return True
    # yapf: enable

  def UpdateAuthors(self):
    """Updates the authors.

    Returns:
      bool: True if the authors update was successful.
    """
    if self._project_name == 'l2tdocs':
      return True

    if not self._projects_helper.UpdateAuthorsFile():
      print('Unable to update authors file.')
      return False

    return True

  def UpdateVersion(self):
    """Updates the version.

    Returns:
      bool: True if the version update was successful.
    """
    if self._project_name == 'l2tdocs':
      return True

    if not self._projects_helper.UpdateVersionFile():
      print('Unable to update version file.')
      return False

    if not self._projects_helper.UpdateDpkgChangelogFile():
      print('Unable to update dpkg changelog file.')
      return False

    return True
