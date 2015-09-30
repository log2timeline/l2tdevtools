#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to manager code reviews."""

from __future__ import print_function
import argparse
import json
import logging
import os
import shlex
import subprocess
import sys
import time
# Keep urllib2 here since we this code should be able to be used
# by a default Python set up.
import urllib2

# Change PYTHONPATH to include utils.
sys.path.insert(0, u'.')

import utils.upload


SUPPORTED_PROJECTS = frozenset([
    u'dfvfs', u'dfwinreg', u'l2tdevtools', u'plaso'])


class CLIHelper(object):
  """Class that defines CLI helper functions."""

  def RunCommand(self, command):
    """Runs a command.

    Args:
      command: string containing the command to run.

    Returns:
      A tuple of the exit code, stdout and stderr file-like objects.
    """
    arguments = shlex.split(command)
    process = subprocess.Popen(
        arguments, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if not process:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return 1, None, None

    output, error = process.communicate()
    if process.returncode != 0:
      logging.error(u'Running: "{0:s}" failed with error: {1:s}.'.format(
          command, error))

    return process.returncode, output, error


class CodeReviewHelper(CLIHelper):
  """Class that defines codereview helper functions."""

  _REVIEW_MAILING_LIST = u'log2timeline-dev@googlegroups.com'

  _REVIEWERS = frozenset([
      u'kiddi@kiddaland.net',
      u'joachim.metz@gmail.com',
      u'onager@deerpie.com'])

  def __init__(self, email_address, no_browser=False):
    """Initializes a codereview helper object.

    Args:
      email_address: string containing the email address.
      no_browser: optional boolean value to indicate if the functionality
                  to use the webbrowser to get the OAuth token should be
                  disabled.
    """
    super(CodeReviewHelper, self).__init__()
    self._access_token = None
    self._email_address = email_address
    self._no_browser = no_browser
    self._upload_py_path = os.path.join(u'utils', u'upload.py')

  def CloseIssue(self, issue_number):
    """Closes the code review issue.

    Args:
      issue_number: an integer containing the codereview issue number.

    Returns:
      A boolean indicating the code review was closed.
    """
    codereview_access_token = self.GetAccessToken()
    if not codereview_access_token:
      return False

    codereview_url = b'https://codereview.appspot.com/{0:d}/close'.format(
        issue_number)

    request = urllib2.Request(codereview_url)

    # Add header: Authorization: OAuth <codereview access token>
    request.add_header(
        u'Authorization', u'OAuth {0:s}'.format(codereview_access_token))

    try:
      url_object = urllib2.urlopen(request)
    except urllib2.HTTPError as exception:
      logging.error(
          u'Failed closing codereview issue: {0:d} with error: {1:s}'.format(
              issue_number, exception))
      return False

    if url_object.code != 200:
      logging.error((
          u'Failed closing codereview issue: {0:d} with status code: '
          u'{1:d}').format(issue_number, url_object.code))
      return False

    return True

  def CreateIssue(self, diffbase, description):
    """Creates a new code review issue.

    Args:
      diffbase: string containing the diffbase.
      description: string containing the description.

    Returns:
      An integer containing the code review number or None.
    """
    reviewers = u','.join(self._REVIEWERS)

    # Remove self from reviewers list.
    try:
      list_index = reviewers.index(self._email_address)
      reviewers.pop(list_index)
    except ValueError:
      pass

    command = u'{0:s} {1:s} --oauth2'.format(
        sys.executable, self._upload_py_path)

    if self._no_browser:
      command = u'{0:s} --no_oauth2_webbrowser'.format(command)

    command = (
        u'{0:s} --send_mail -r {1:s} --cc {2:s} -t "{3:s}" -y -- '
        u'{4:s}').format(
            command, reviewers, self._REVIEW_MAILING_LIST, description,
            diffbase)

    if self._no_browser:
      print(
          u'Upload server: codereview.appspot.com (change with -s/--server)\n'
          u'Go to the following link in your browser:\n'
          u'\n'
          u'    https://codereview.appspot.com/get-access-token\n'
          u'\n'
          u'and copy the access token.\n'
          u'\n')
      print(u'Enter access token:', end=u' ')

    exit_code, output, _ = self.RunCommand(command)
    print(output)

    if exit_code != 0:
      return

    issue_url_line_start = (
        u'Issue created. URL: http://codereview.appspot.com/')
    for line in output.split(b'\n'):
      if line.startswith(issue_url_line_start):
        try:
          return int(line[len(issue_url_line_start):], 10)
        except ValueError:
          pass

  def GetAccessToken(self):
    """Retrieves the OAuth access token.

    Returns:
      String containing a codereview access token.
    """
    if not self._access_token:
      # TODO: add support to get access token directly from user.
      self._access_token = utils.upload.GetAccessToken()
      if not self._access_token:
        logging.error(u'Unable to retrieve access token.')

    return self._access_token

  def QueryIssue(self, issue_number):
    """Queries a code review issue.

    Args:
      issue_number: an integer containing the codereview issue number.

    Returns:
      A dictonary containing the JSON response or None.
    """
    codereview_url = b'https://codereview.appspot.com/api/{0:d}'.format(
        issue_number)

    request = urllib2.Request(codereview_url)

    try:
      url_object = urllib2.urlopen(request)
    except urllib2.HTTPError as exception:
      logging.error(
          u'Failed querying codereview issue: {0:d} with error: {1:s}'.format(
              issue_number, exception))
      return

    if url_object.code != 200:
      logging.error((
          u'Failed querying codereview issue: {0:d} with status code: '
          u'{1:d}').format(issue_number, url_object.code))
      return

    response_data = url_object.read()
    return json.loads(response_data)

  def UpdateIssue(self, issue_number, diffbase, description):
    """Updates a new code review issue.

    Args:
      issue_number: an integer containing the codereview issue number.
      diffbase: string containing the diffbase.
      description: string containing the description.

    Returns:
      A boolean indicating the code review was updated.
    """
    command = u'{0:s} {1:s} --oauth2'.format(
        sys.executable, self._upload_py_path)

    if self._no_browser:
      command = u'{0:s} --no_oauth2_webbrowser'.format(command)

    command = (
        u'{0:s} -i {1:d} -m "Code updated." -t "{2:s}" -y -- '
        u'{3:s}').format(command, issue_number, description, diffbase)

    exit_code, output, _ = self.RunCommand(command)
    print(output)

    return exit_code == 0


class GitHelper(CLIHelper):
  """Class that defines git helper functions."""

  def __init__(self, git_repo_url):
    """Initializes a git helper object.

    Args:
      git_repo_url: string containing the git repo url.
    """
    super(GitHelper, self).__init__()
    self._git_repo_url = git_repo_url
    self._remotes = []

  def _GetRemotes(self):
    """Retrieves the git repo remotes.

    Returns:
      A list of string containing the remotes or None.
    """
    if not self._remotes:
      exit_code, output, _ = self.RunCommand(u'git remote -v')
      if exit_code == 0:
        self._remotes = output.split(b'\n')

    return self._remotes

  def AddPath(self, path):
    """Adds a specific path to be managed by git.

    Args:
      path: string containing the path.

    Returns:
      A boolean indicating the path was added.
    """
    command = u'git add -A {0:s}'.format(path)
    exit_code, _, _ = self.RunCommand(command)
    return exit_code == 0

  def CheckHasBranch(self, branch):
    """Checks if the git repo has a specific branch.

    Args:
      branch: name of the feature branch.

    Returns:
      A boolean indicating the git repo has the specific branch.
    """
    exit_code, output, _ = self.RunCommand(u'git branch')
    if exit_code != 0:
      return False

    # Check for remote entries starting with upstream.
    for line in output.split(b'\n'):
      # Ignore the first 2 characters of the line.
      if line[2:] == branch:
        return True
    return False

  def CheckHasProjectOrigin(self):
    """Checks if the git repo has the project remote origin defined.

    Returns:
      A boolean indicating the git repo has the project origin defined.
    """
    origin_git_repo_url = self.GetRemoteOrigin()
    return origin_git_repo_url == self._git_repo_url

  def CheckHasProjectUpstream(self):
    """Checks if the git repo has the project remote upstream defined.

    Returns:
      A boolean indicating the git repo has the project remote upstream
      defined.
    """
    # Check for remote entries starting with upstream.
    for remote in self._GetRemotes():
      if remote.startswith(b'upstream\t{0:s}'.format(self._git_repo_url)):
        return True
    return False

  def CheckHasUncommittedChanges(self):
    """Checks if the git repo has uncommitted changes.

    Returns:
      A boolean indicating the git repo has uncommitted changes.
    """
    exit_code, output, _ = self.RunCommand(u'git status -s')
    if exit_code != 0:
      return False

    # Check if 'git status -s' yielded any output.
    for line in output.split(b'\n'):
      if line:
        return True
    return False

  def CheckSynchronizedWithUpstream(self):
    """Checks if the git repo is synchronized with upstream.

    Returns:
      A boolean indicating the git repo is synchronized with upstream.
    """
    # Fetch the entire upstream repo information not only that of
    # the master branch. Otherwise the information about the current
    # upstream HEAD is not updated.
    exit_code, _, _ = self.RunCommand(u'git fetch upstream')
    if exit_code != 0:
      return False

    # The result of "git log HEAD..upstream/master --oneline" should be empty
    # if the git repo is synchronized with upstream.
    exit_code, output, _ = self.RunCommand(
        u'git log HEAD..upstream/master --oneline')
    return exit_code == 0 and not output

  def DropUncommittedChanges(self):
    """Drops the uncommitted changes."""
    self.RunCommand(u'git stash && git stash drop')

  def GetActiveBranch(self):
    """Retrieves the active branch.

    Returns:
      String containing the name of the active branch or None.
    """
    exit_code, output, _ = self.RunCommand(u'git branch')
    if exit_code != 0:
      return False

    # Check for remote entries starting with upstream.
    for line in output.split(b'\n'):
      if line.startswith(b'* '):
        # Ignore the first 2 characters of the line.
        return line[2:]
    return

  def GetChangedFiles(self, diffbase):
    """Retrieves the changed files.

    Args:
      diffbase: string containing the git diffbase e.g. upstream/master.

    Returns:
      List containing string with the names of the changed files.
    """
    exit_code, output, _ = self.RunCommand(
        u'git diff --name-only {0:s}'.format(diffbase))
    if exit_code != 0:
      return []

    return output.split(b'\n')

  def GetChangedPythonFiles(self, diffbase):
    """Retrieves the changed Python files.

    Args:
      diffbase: string containing the git diffbase e.g. upstream/master.

    Returns:
      List containing string with the names of the changed Python files.
    """
    upload_path = os.path.join(u'utils', u'upload.py')
    python_files = []
    for changed_file in self.GetChangedFiles(diffbase):
      if (not changed_file.endswith(u'.py') or
          changed_file.endswith(u'_pb2.py') or
          not os.path.exists(changed_file) or
          changed_file.startswith(u'test_data') or
          changed_file in [u'setup.py', upload_path]):
        continue

      python_files.append(changed_file)

    return python_files

  def GetEmailAddress(self):
    """Retrieves the email address.

    Returns:
      A string containing the email address or None.
    """
    exit_code, output, _ = self.RunCommand(u'git config user.email')
    if exit_code != 0:
      return

    output_lines = output.split(b'\n')
    if len(output_lines) != 1:
      return

    return output_lines[0]

  def GetLastCommitMessage(self):
    """Retrieves the last commit message.

    Returns:
      A string containing the last commit message or None.
    """
    exit_code, output, _ = self.RunCommand(u'git log -1')
    if exit_code != 0:
      return

    # Expecting 6 lines of output where the 5th line contains
    # the commit message.
    output_lines = output.split(b'\n')
    if len(output_lines) != 6:
      return

    return output_lines[4].strip()

  def GetRemoteOrigin(self):
    """Retrieves the remote origin.

    Returns:
      A string containing the git repo URL or None.
    """
    # Check for remote entries starting with origin.
    for remote in self._GetRemotes():
      if remote.startswith(b'origin\t'):
        values = remote.split()
        if len(values) == 3:
          return values[1]

  def PullFromFork(self, git_repo_url, branch):
    """Pulls changes from a feature branch on a fork.

    Args:
      git_repo_url: string containing the git repo url of the fork.
      branch: name of the feature branch of the fork.

    Returns:
      A boolean indicating the pull was successful.
    """
    command = u'git pull --squash {0:s} {1:s}'.format(git_repo_url, branch)
    exit_code, _, _ = self.RunCommand(command)
    return exit_code == 0

  def PushToOrigin(self, branch, force=False):
    """Forces a push of the active branch of the git repo to origin.

    Args:
    Args:
      branch: name of the feature branch.
      force: optional boolean value to indicate the push should be forced.

    Returns:
      A boolean indicating the push was successful.
    """
    if force:
      command = u'git push --set-upstream origi {0:s}'.format(branch)
    else:
      command = u'git push -f --set-upstream origin {0:s}'.format(branch)

    exit_code, _, _ = self.RunCommand(command)
    return exit_code == 0

  def RemoveFeatureBranch(self, branch):
    """Removes the git feature branch both local and from origin.

    Args:
      branch: name of the feature branch.
    """
    if branch == u'master':
      return

    self.RunCommand(u'git push origin --delete {0:s}'.format(branch))
    self.RunCommand(u'git branch -D {0:s}'.format(branch))

  def SynchronizeWithOrigin(self):
    """Synchronizes git with origin.

    Returns:
      A boolean indicating the git repo has synchronized with origin.
    """
    exit_code, _, _ = self.RunCommand(u'git fetch origin')
    if exit_code != 0:
      return False

    exit_code, _, _ = self.RunCommand(
        u'git pull --no-edit origin master')

    return exit_code == 0

  def SynchronizeWithUpstream(self):
    """Synchronizes git with upstream.

    Returns:
      A boolean indicating the git repo has synchronized with upstream.
    """
    exit_code, _, _ = self.RunCommand(u'git fetch upstream')
    if exit_code != 0:
      return False

    exit_code, _, _ = self.RunCommand(
        u'git pull --no-edit --rebase upstream master')
    if exit_code != 0:
      return False

    exit_code, _, _ = self.RunCommand(u'git push')

    return exit_code == 0

  def SwitchToMasterBranch(self):
    """Switches git to the master branch.

    Returns:
      A boolean indicating the git repo has switched to the master branch.
    """
    exit_code, _, _ = self.RunCommand(u'git checkout master')
    return exit_code != 0


class GitHubHelper(object):
  """Class that defines github helper functions."""

  def __init__(self, organization, project):
    """Initializes a github helper object.

    Args:
      organization: string containing the github organization name.
      project: string containing the github project name.
    """
    super(GitHubHelper, self).__init__()
    self._organization = organization
    self._project = project

  def CreatePullRequest(
      self, access_token, codereview_issue_number, origin, description):
    """Creates a pull request.

    Args:
      access_token: string containing the github access token.
      codereview_issue_number: an integer containing the codereview
                               issue number.
      origin: a string containing the origin of the pull request e.g.
              "username:feature".
      description: a string containing the description.

    Returns:
      A boolean indicating the pull request was created.
    """
    title = b'{0:d}: {1:s}'.format(codereview_issue_number, description)
    body = (
        b'[Code review: {0:d}: {1:s}]'
        b'(https://codereview.appspot.com/{0:d}/)').format(
            codereview_issue_number, description)

    post_data = (
        b'{{\n'
        b'  "title": "{0:s}",\n'
        b'  "body": "{1:s}",\n'
        b'  "head": "{2:s}",\n'
        b'  "base": "master"\n'
        b'}}\n').format(title, body, origin)

    github_url = (
        u'https://api.github.com/repos/{0:s}/{1:s}/pulls?'
        u'access_token={2:s}').format(
            self._organization, self._project, access_token)

    request = urllib2.Request(github_url)

    # This will change the request into a POST.
    request.add_data(post_data)

    try:
      url_object = urllib2.urlopen(request)
    except urllib2.HTTPError as exception:
      logging.error(
          u'Failed creating pull request: {0:d} with error: {1:s}'.format(
              codereview_issue_number, exception))
      return False

    if url_object.code != 200:
      # TODO: determine why this is failing while PR is created.
      logging.error(
          u'Failed creating pull request: {0:d} with status code: {1:d}'.format(
              codereview_issue_number, url_object.code))
      return False

    return True

  def GetForkGitRepoUrl(self, username):
    """Retrieves the git repo URL of a fork.

    Args:
      username: string containing the github username of the fork.

    Returns:
      A string containing the git repo URL or None.
    """
    return u'https://github.com/{0:s}/{1:s}.git'.format(username, self._project)

  def QueryUser(self, username):
    """Queries a github user.

    Args:
      username: a github user name.

    Returns:
      A dictonary containing the JSON response or None.
    """
    github_url = b'https://api.github.com/users/{0:s}'.format(username)

    request = urllib2.Request(github_url)

    try:
      url_object = urllib2.urlopen(request)
    except urllib2.HTTPError as exception:
      logging.error(
          u'Failed querying github user: {0:s} with error: {1:s}'.format(
              username, exception))
      return

    if url_object.code != 200:
      logging.error(
          u'Failed querying github user: {0:d} with status code: {1:d}'.format(
              username, url_object.code))
      return

    response_data = url_object.read()
    return json.loads(response_data)


class PylintHelper(CLIHelper):
  """Class that defines pylint helper functions."""

  _MINIMUM_VERSION_TUPLE = (1, 4, 0)

  def CheckFiles(self, filenames):
    """Checks if the linting of the files is correct using pylint.

    Args:
      filenames: list of strings with file names.

    Returns:
      A boolean indicating the git repo has the specific branch.
    """
    print(u'Running linter on changed files.')
    failed_filenames = []
    for filename in filenames:
      print(u'Checking: {0:s}'.format(filename))

      command = u'pylint --rcfile=utils/pylintrc {0:s}'.format(filename)
      exit_code = subprocess.call(command, shell=True)
      if exit_code != 0:
        failed_filenames.append(filename)

    if failed_filenames:
      print(u'\nFiles with linter errors:\n{0:s}\n'.format(
          u'\n'.join(failed_filenames)))
      return False

    return True

  def CheckUpToDateVersion(self):
    """Checks if the pylint version is up to date.

    Returns:
      A boolean indicating the version is up to date.
    """
    exit_code, output, _ = self.RunCommand(u'pylint --version')
    if exit_code != 0:
      return False

    version_tuple = (0, 0, 0)
    for line in output.split(b'\n'):
      if line.startswith(b'pylint '):
        _, _, version = line.partition(b' ')
        # Remove a trailing comma.
        version, _, _ = version.partition(b',')

        version_tuple = tuple([int(digit) for digit in version.split(b'.')])

    return version_tuple >= self._MINIMUM_VERSION_TUPLE


class SphinxAPIDocHelper(CLIHelper):
  """Class that defines sphinx-apidoc helper functions."""

  _MINIMUM_VERSION_TUPLE = (1, 2, 0)

  def CheckUpToDateVersion(self):
    """Checks if the sphinx-apidoc version is up to date.

    Returns:
      A boolean indicating the version is up to date.
    """
    exit_code, output, _ = self.RunCommand(u'sphinx-apidoc --version')
    if exit_code != 0:
      return False

    version_tuple = (0, 0, 0)
    for line in output.split(b'\n'):
      if line.startswith(b'Sphinx (sphinx-apidoc) '):
        _, _, version = line.rpartition(b' ')

        version_tuple = tuple([int(digit) for digit in version.split(b'.')])

    return version_tuple >= self._MINIMUM_VERSION_TUPLE

  def UpdateAPIDocs(self):
    """Updates the API docs."""
    # TODO: implement.
    command = u'sphinx-apidoc -f -o docs {0:s}'.format(self._project_name)


class NetRCFile(object):
  """Class that defines a .netrc file."""

  def __init__(self):
    """Initializes a .netrc file object."""
    super(NetRCFile, self).__init__()
    self._contents = None
    self._values = None

    home_path = os.path.expanduser(u'~')
    self._path = os.path.join(home_path, u'.netrc')
    if not os.path.exists(self._path):
      return

    with open(self._path, 'r') as file_object:
      self._contents = file_object.read()

  def _GetGitHubValues(self):
    """Retrieves the github values."""
    if not self._contents:
      return

    if not self._values:
      for line in self._contents.split(b'\n'):
        if line.startswith(b'machine github.com '):
          self._values = line.split(b' ')
          break

    return self._values[2:]

  def GetGitHubAccessToken(self):
    """Retrieves the github access token.

    Returns:
      A string containing the github access token or None.
    """
    values = self._GetGitHubValues()
    if not values:
      return

    for value_index, value in enumerate(values):
      if value == u'password':
        return values[value_index + 1]

  def GetGitHubUsername(self):
    """Retrieves the github username.

    Returns:
      A string containing the github username or None.
    """
    values = self._GetGitHubValues()
    if not values:
      return

    for value_index, value in enumerate(values):
      if value == u'username':
        return values[value_index + 1]


class ReviewFile(object):
  """Class that defines a review file."""

  def __init__(self, branch_name):
    """Initializes a review file object.

    Args:
      branch_name: string containing the name of the feature branch of
                   the review.
    """
    super(ReviewFile, self).__init__()
    self._contents = None

    self._path = os.path.join(u'.review', branch_name)
    if not os.path.exists(self._path):
      return

    with open(self._path, 'r') as file_object:
      self._contents = file_object.read()

  def Create(self, codereview_issue_number):
    """Creates a new review file.

    Args:
      codereview_issue_number: an integer containing the codereview
                               issue number.

    Returns:
      A boolean indicating the review file was created.
    """
    with open(self._path, 'w') as file_object:
      file_object.write(u'{0:d}'.format(codereview_issue_number))

  def GetCodeReviewIssueNumber(self):
    """Retrieves the codereview issue number.

    Returns:
      An integer containing the codereview issue number.
    """
    if not self._contents:
      return

    try:
      return int(self._contents, 10)
    except ValueError:
      pass

  def Remove(self):
    """Removes the review file."""
    if not os.path.exists(self._path):
      return

    os.remove(self._path)


def Main():
  argument_parser = argparse.ArgumentParser(
      description=u'Script to manage code reviews.')

  # TODO: add option to directly pass code review issue number.

  argument_parser.add_argument(
      u'--diffbase', dest=u'diffbase', action=u'store', type=unicode,
      metavar=u'DIFFBASE', default=u'upstream/master', help=(
          u'The diffbase the default is upstream/master. This options is used '
          u'to indicate to what "base" the code changes are relative to and '
          u'can be used to "chain" code reviews.'))

  argument_parser.add_argument(
      u'--nobrowser', u'--no-browser', u'--no_browser', dest=u'no_browser',
      action=u'store_true', default=False, help=(
          u'disable the functionality to use the webbrowser to get the OAuth '
          u'token should be disabled.'))

  commands_parser = argument_parser.add_subparsers(dest=u'command')

  close_command_parser = commands_parser.add_parser(u'close')

  # TODO: add this to help output.
  close_command_parser.add_argument(
      u'branch', action=u'store', metavar=u'BRANCH', default=None,
      help=(u'name of the corresponding feature branch.'))

  commands_parser.add_parser(u'create')

  merge_command_parser = commands_parser.add_parser(u'merge')

  # TODO: add this to help output.
  merge_command_parser.add_argument(
      u'codereview_issue_number', action=u'store',
      metavar=u'CODEREVIEW_ISSIE_NUMBER', default=None,
      help=(u'the codereview issue number to be merged.'))

  # TODO: add this to help output.
  merge_command_parser.add_argument(
      u'github_origin', action=u'store',
      metavar=u'GITHUB_ORIGIN', default=None,
      help=(u'the github origin to merged e.g. username:feature.'))

  # TODO: add dry-run option to run merge without commit.
  # useful to test pending CLs.

  commands_parser.add_parser(u'update')

  options = argument_parser.parse_args()

  print_help_on_error = False
  if options.command == u'close':
    close_feature_branch = getattr(options, u'branch', None)
    if not close_feature_branch:
      print(u'Feature branch value is missing.')
      print_help_on_error = True

  elif options.command == u'merge':
    merge_codereview_issue_number = getattr(
        options, u'codereview_issue_number', None)
    if not merge_codereview_issue_number:
      print(u'Codereview issue number value is missing.')
      print_help_on_error = True

    merge_github_origin = getattr(options, u'github_origin', None)
    if not merge_github_origin:
      print(u'Github origin value is missing.')
      print_help_on_error = True

  if print_help_on_error:
    print(u'')
    argument_parser.print_help()
    print(u'')
    return False

  home_path = os.path.expanduser(u'~')
  netrc_path = os.path.join(home_path, u'.netrc')
  if not os.path.exists(netrc_path):
    print(u'{0:s} aborted - unable to find .netrc.'.format(
        options.command.title()))
    return False

  project_name = os.path.abspath(__file__)
  project_name = os.path.dirname(project_name)
  project_name = os.path.dirname(project_name)
  project_name = os.path.basename(project_name)

  if not project_name in SUPPORTED_PROJECTS:
    print(u'{0:s} aborted - unsupported project name: {1:s}.'.format(
        options.command.title(), project_name))
    return False

  git_repo_url = b'https://github.com/log2timeline/{0:s}.git'.format(
      project_name)

  git_helper = GitHelper(git_repo_url)

  if options.command in [u'close', u'create', u'update']:
    if not git_helper.CheckHasProjectUpstream():
      print(u'{0:s} aborted - missing project upstream.'.format(
          options.command.title()))
      print(u'Run: git remote add upstream {0:s}'.format(git_repo_url))
      return False

  elif options.command == u'merge':
    if not git_helper.CheckHasProjectOrigin():
      print(u'{0:s} aborted - missing project origin.'.format(
          options.command.title()))
      return False

  if git_helper.CheckHasUncommittedChanges():
    print(u'{0:s} aborted - detected uncommitted changes.'.format(
        options.command.title()))
    print(u'Run: git commit')
    return False

  active_branch = git_helper.GetActiveBranch()
  if options.command in [u'create', u'update']:
    if active_branch == u'master':
      print(u'{0:s} aborted - active branch is master.'.format(
          options.command.title()))
      return False

  elif options.command == u'close':
    if close_feature_branch == u'master':
      print(u'{0:s} aborted - feature branch cannot be master.'.format(
          options.command.title()))
      return False

    if active_branch != u'master':
      git_helper.SwitchToMasterBranch()
      active_branch = u'master'

  github_helper = GitHubHelper(u'log2timeline', project_name)

  if options.command in [u'create', u'close', u'update']:
    if not git_helper.CheckSynchronizedWithUpstream():
      if not git_helper.SynchronizeWithUpstream():
        print((
            u'{0:s} aborted - unable to synchronize with '
            u'upstream/master.').format(options.command.title()))
        return False

      force_push = True
    else:
      force_push = False

    if not git_helper.PushToOrigin(active_branch, force=force_push):
      print(u'{0:s} aborted - unable to push updates to origin/{1:s}.'.format(
          options.command.title(), active_branch))
      return False

  elif options.command == u'merge':
    if not git_helper.SynchronizeWithOrigin():
      print((
          u'{0:s} aborted - unable to synchronize with '
          u'origin/master.').format(options.command.title()))
      return False

    codereview_helper = CodeReviewHelper(no_browser=options.no_browser)
    codereview_information = codereview_helper.QueryIssue(
        merge_codereview_issue_number)
    if not codereview_information:
      print((
          u'{0:s} aborted - unable to retrieve code review: {1:d} '
          u'information.').format(
              options.command.title(), merge_codereview_issue_number))
      return False

    merge_description = codereview_information.get(u'subject', None)
    if not merge_description:
      print((
          u'{0:s} aborted - unable to determine description of code review: '
          u'{1:d}.').format(
              options.command.title(), merge_codereview_issue_number))
      return False

    merge_email_address = codereview_information.get(u'owner_email', None)
    if not merge_email_address:
      print((
          u'{0:s} aborted - unable to determine email address of owner of '
          u'code review: {1:d}.').format(
              options.command.title(), merge_codereview_issue_number))
      return False

    fork_username, _, fork_feature_branch = merge_github_origin.partition(u':')

    github_user_information = github_helper.QueryUser(fork_username)
    if not github_user_information:
      print((
          u'{0:s} aborted - unable to retrieve github user: {1:s} '
          u'information.').format(options.command.title(), fork_username))
      return False

    merge_fullname = github_user_information.get(u'name', None)
    if not merge_fullname:
      merge_fullname = codereview_information.get(u'owner', None)
    if not merge_fullname:
      merge_fullname = github_user_information.get(u'company', None)
    if not merge_fullname:
      print((
          u'{0:s} aborted - unable to determine full name.').format(
              options.command.title()))
      return False

    merge_author = u'{0:s} <{1:s}>'.format(merge_fullname, merge_email_address)

  if options.command == u'merge':
    sphinxapidoc_helper = SphinxAPIDocHelper()
    if not sphinxapidoc_helper.CheckUpToDateVersion():
      print(u'{0:s} aborted - sphinx-apidoc verion 1.2.0 or later required.'.format(
          options.command.title()))
      return False

  if options.command in [u'create', u'merge', u'update']:
    pylint_helper = PylintHelper()
    if not pylint_helper.CheckUpToDateVersion():
      print(u'{0:s} aborted - pylint verion 1.4.0 or later required.'.format(
          options.command.title()))
      return False

    if options.command == u'merge':
      fork_git_repo_url = github_helper.GetForkGitRepoUrl(fork_username)

      if not git_helper.PullFromFork(fork_git_repo_url, fork_feature_branch):
        print(u'{0:s} aborted - unable to pull changes from fork.'.format(
            options.command.title()))
        return False

      changed_python_files = git_helper.GetChangedPythonFiles(u'origin/master')
    else:
      changed_python_files = git_helper.GetChangedPythonFiles(options.diffbase)

    if not pylint_helper.CheckFiles(changed_python_files):
      print(u'{0:s} aborted - unable to pass linter.'.format(
          options.command.title()))

      if options.command == u'merge':
        git_helper.DropUncommittedChanges()
      return False

    # TODO: determine why this alters the behavior of argparse.
    command = u'{0:s} run_tests.py'.format(sys.executable)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      print(u'{0:s} aborted - unable to pass tests.'.format(
          options.command.title()))

      if options.command == u'merge':
        git_helper.DropUncommittedChanges()
      return False

  if options.command == u'create':
    git_origin = git_helper.GetRemoteOrigin()
    if not git_origin.startswith(u'https://github.com/'):
      print(u'{0:s} aborted - unsupported git remote origin: {1:s}'.format(
          options.command.title(), git_origin))
      print(u'Make sure the git remote origin is hosted on github.com')
      return False

    git_origin, _, _ = git_origin[len(u'https://github.com/'):].rpartition(u'/')

    netrc_file = NetRCFile()
    github_access_token = netrc_file.GetGitHubAccessToken()
    if not github_access_token:
      print(u'{0:s} aborted - unable to determine github access token.'.format(
          options.command.title()))
      print(u'Make sure .netrc is configured with a github access token.')
      return False

    last_commit_message = git_helper.GetLastCommitMessage()
    print(u'Automatic generated description of code review:')
    print(last_commit_message)
    print(u'')

    print(u'Enter a description for the code review or hit enter to use the')
    print(u'automatic generated one:')
    user_input = sys.stdin.readline()
    user_input = user_input.strip()

    if not user_input:
      description = last_commit_message
    else:
      description = user_input

    email_address = git_helper.GetEmailAddress()
    codereview_helper = CodeReviewHelper(
        email_address, no_browser=options.no_browser)
    codereview_issue_number = codereview_helper.CreateIssue(
        options.diffbase, description)

    if not os.path.isdir(u'.review'):
      os.mkdir(u'.review')

    review_file = ReviewFile(active_branch)
    review_file.Create(codereview_issue_number)

    create_github_origin = u'{0:s}:{1:s}'.format(git_origin, active_branch)
    if github_helper.CreatePullRequest(
        github_access_token, codereview_issue_number, create_github_origin,
        description):
      print(u'Unable to create pull request.')

  elif options.command == u'close':
    if not git_helper.CheckHasBranch(close_feature_branch):
      print(u'No such feature branch: {0:s}'.format(close_feature_branch))
    else:
      git_helper.RemoveFeatureBranch(close_feature_branch)

    review_file = ReviewFile(close_feature_branch)
    codereview_issue_number = review_file.GetCodeReviewIssueNumber()
    review_file.Remove()

    if codereview_issue_number:
      if not codereview_helper.CloseIssue(codereview_issue_number):
        print(u'Unable to close code review: {0:d}'.format(
            codereview_issue_number))
        print((
            u'Close it manually on: https://codereview.appspot.com/'
            u'{0:d}').format(codereview_issue_number))

  elif options.command == u'merge':
    # TODO: refactor into separate function/class?
    version_file_path = os.path.join(project_name, u'__init__.py')
    if not is.path.exists(version_file_path):
      # TODO: error
      git_helper.DropUncommittedChanges()

    try:
      with open(version_file_path, u'rb') as file_object:
        version_file_contents = file_object.read()

    except IOError as exception:
      print(u'Unable to read version file with error: {0:s}'.format(
          exception))
        git_helper.DropUncommittedChanges()

    date_version = time.strftime(u'%Y%m%d')
    # TODO: catch decode error.
    version_file_contents = version_file_contents.decode('utf-8')
    lines = version_file_contents.split(u'\n')

    for line_index, line in enumerate(lines):
      if project == u'plaso' and line.startswith(u'VERSION_DATE = '):
        version_string = u'VERSION_DATE = \'{0:s}\''.format(date_version)
        line[line_index] = version_string

      else project != u'plaso' and line.startswith(u'__version__ = '):
        version_string = u'__version__ = \'{0:s}\''.format(date_version)
        line[line_index] = version_string

    # TODO: catch encode error.
    version_file_contents = version_file_contents.encode(u'utf-8')

    try:
      with open(version_file_path, u'wb') as file_object:
        file_object.write(version_file_contents)

    except IOError as exception:
      print(u'Unable to write version file with error: {0:s}'.format(
          exception))
        git_helper.DropUncommittedChanges()

    # TODO: refactor into separate function/class?
    dpkg_changelog_path = os.path.join(u'config', u'dpkg', u'changelog')
    if os.path.exists(dpkg_changelog_path):
      dpkg_date = time.strftime(u'%a, %d %b %Y %H:%M:%S %z')
      dpkg_maintainter = u'Log2Timeline <log2timeline-dev@googlegroups.com>'
      dpkg_changelog_content = u'\n'.join([
          u'python-{0:s} ({1:s}-1) unstable; urgency=low'.format(
              project_name, project_version),
          u'',
          u'  * Auto-generated',
          u'',
          u' -- {0:s}  {1:s}'.format(dpkg_maintainter, dpkg_date)])

      # TODO: catch encode error.
      dpkg_changelog_content = dpkg_changelog_content.encode(u'utf-8')

      try:
        with open(dpkg_changelog_path, u'wb') as file_object:
          file_object.write(dpkg_changelog_content)
      except IOError as exception:
        print(u'Unable to write dpkg changelog file with error: {0:s}'.format(
            exception))
        git_helper.DropUncommittedChanges()

    # On error: git stash && git stash drop
    # git_helper.DropUncommittedChanges()

    apidoc_config_path = os.path.join(u'docs', u'conf.py')
    if os.path.exists(apidoc_config_path):
      sphinxapidoc_helper.UpdateAPIDocs()

      git_helper.AddPath(u'docs')

      # Trigger a readthedocs build for the docs.
      # The plaso readthedocs content is mirrored with the wiki repo
      # and has no trigger on update webhook for readthedocs.
      # TODO: curl -X POST http://readthedocs.org/build/plaso

    # TODO: commit changes.
    _ = merge_description
    _ = merge_author

    # TODO: add commit message to codereview

  elif options.command == u'update':
    review_file = ReviewFile(active_branch)
    codereview_issue_number = review_file.GetCodeReviewIssueNumber()

    last_commit_message = git_helper.GetLastCommitMessage()
    print(u'Automatic generated description of the update:')
    print(last_commit_message)
    print(u'')

    print(u'Enter a description for the update or hit enter to use the')
    print(u'automatic generated one:')
    user_input = sys.stdin.readline()
    user_input = user_input.strip()

    if not user_input:
      description = last_commit_message
    else:
      description = user_input

    email_address = git_helper.GetEmailAddress()
    codereview_helper = CodeReviewHelper(
        email_address, no_browser=options.no_browser)
    if not codereview_helper.UpdateIssue(
        codereview_issue_number, options.diffbase, description):
      print(u'Unable to update code review: {0:d}'.format(
          codereview_issue_number))
      return False

  return True


if __name__ == u'__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
