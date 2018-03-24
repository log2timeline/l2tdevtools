# -*- coding: utf-8 -*-
"""Helper for interacting with git."""

from __future__ import unicode_literals

import os

from l2tdevtools.review_helpers import cli


class GitHelper(cli.CLIHelper):
  """Git command helper."""

  def __init__(self, git_repo_url):
    """Initializes a git helper.

    Args:
      git_repo_url (str): git repo URL.
    """
    super(GitHelper, self).__init__()
    self._git_repo_url = git_repo_url
    self._remotes = []

  def _GetRemotes(self):
    """Retrieves the git repository remotes.

    Returns:
      list[str]: git repository remotes or None.
    """
    if not self._remotes:
      exit_code, output, _ = self.RunCommand('git remote -v')
      if exit_code == 0:
        self._remotes = list(filter(None, output.split(b'\n')))

    return self._remotes

  def AddPath(self, path):
    """Adds a specific path to be managed by git.

    Args:
      path (str): path.

    Returns:
      bool: True if the path was added.
    """
    command = 'git add -A {0:s}'.format(path)
    exit_code, _, _ = self.RunCommand(command)
    return exit_code == 0

  def CheckHasBranch(self, branch):
    """Checks if the git repo has a specific branch.

    Args:
      branch (str): name of the feature branch.

    Returns:
      bool: True if git repo has the specific branch.
    """
    exit_code, output, _ = self.RunCommand('git branch')
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
      bool: True if the git repo has the project origin defined.
    """
    origin_git_repo_url = self.GetRemoteOrigin()

    is_match = origin_git_repo_url == self._git_repo_url
    if not is_match:
      is_match = origin_git_repo_url == self._git_repo_url[:-4]

    return is_match

  def CheckHasProjectUpstream(self):
    """Checks if the git repo has the project remote upstream defined.

    Returns:
      bool: True if the git repo has the project remote upstream defined.
    """
    # Check for remote entries starting with upstream.
    for remote in self._GetRemotes():
      if remote.startswith(b'upstream\t{0:s}'.format(self._git_repo_url)):
        return True
    return False

  def CheckHasUncommittedChanges(self):
    """Checks if the git repo has uncommitted changes.

    Returns:
      bool: True if the git repo has uncommitted changes.
    """
    exit_code, output, _ = self.RunCommand('git status -s')
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
      bool: True if the git repo is synchronized with upstream.
    """
    # Fetch the entire upstream repo information not only that of
    # the master branch. Otherwise the information about the current
    # upstream HEAD is not updated.
    exit_code, _, _ = self.RunCommand('git fetch upstream')
    if exit_code != 0:
      return False

    # The result of "git log HEAD..upstream/master --oneline" should be empty
    # if the git repo is synchronized with upstream.
    exit_code, output, _ = self.RunCommand(
        'git log HEAD..upstream/master --oneline')
    return exit_code == 0 and not output

  def CommitToOriginInNameOf(
      self, codereview_issue_number, author, description):
    """Commits changes in name of an author to the master branch of origin.

    Args:
      codereview_issue_number (int|str): codereview issue number.
      author (str): full name and email address of the author, formatted as:
          "Full Name <email.address@example.com>".
      description (str): description of the commit.

    Returns:
      bool: True if the changes were committed to the git repository.
    """
    command = (
        'git commit -a --author="{0:s}" '
        '-m "Code review: {1:s}: {2:s}"').format(
            author, codereview_issue_number, description)
    exit_code, _, _ = self.RunCommand(command)
    if exit_code != 0:
      return False

    exit_code, _, _ = self.RunCommand(u'git push origin master')
    if exit_code != 0:
      return False

    return True

  def DropUncommittedChanges(self):
    """Drops the uncommitted changes."""
    self.RunCommand('git stash')
    self.RunCommand('git stash drop')

  def GetActiveBranch(self):
    """Retrieves the active branch.

    Returns:
      str: name of the active branch or None.
    """
    exit_code, output, _ = self.RunCommand('git branch')
    if exit_code != 0:
      return False

    # Check for remote entries starting with upstream.
    for line in output.split(b'\n'):
      if line.startswith(b'* '):
        # Ignore the first 2 characters of the line.
        return line[2:]
    return

  def GetChangedFiles(self, diffbase=None):
    """Retrieves the changed files.

    Args:
      diffbase (Optional[str]): git diffbase, for example "upstream/master".

    Returns:
      list[str]: names of the changed files.
    """
    if diffbase:
      command = 'git diff --name-only {0:s}'.format(diffbase)
    else:
      command = 'git ls-files'

    exit_code, output, _ = self.RunCommand(command)
    if exit_code != 0:
      return []

    return output.split(b'\n')

  def GetChangedPythonFiles(self, diffbase=None):
    """Retrieves the changed Python files.

    Note that several Python files are excluded:
    * Python files generated by the protobuf compiler (*_pb2.py)
    * Python files used as test data (test_data/*.py)
    * setup.py and review/lib/upload.py

    Args:
      diffbase (Optional[str]): git diffbase, for example "upstream/master".

    Returns:
      list[str]: names of the changed Python files.
    """
    upload_path = os.path.join('l2tdevtools', 'lib', 'upload.py')
    python_files = []
    for changed_file in self.GetChangedFiles(diffbase=diffbase):
      if (not changed_file.endswith('.py') or
          changed_file.endswith('_pb2.py') or
          not os.path.exists(changed_file) or
          changed_file.startswith('data') or
          changed_file.startswith('docs') or
          changed_file.startswith('test_data') or
          changed_file in ('setup.py', upload_path)):
        continue

      python_files.append(changed_file)

    return python_files

  def GetEmailAddress(self):
    """Retrieves the email address.

    Returns:
      str: email address or None.
    """
    exit_code, output, _ = self.RunCommand('git config user.email')
    if exit_code != 0:
      return

    output_lines = output.split(b'\n')
    if not output_lines:
      return

    return output_lines[0]

  def GetLastCommitMessage(self):
    """Retrieves the last commit message.

    Returns:
      str: last commit message or None.
    """
    exit_code, output, _ = self.RunCommand('git log -1')
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
      str: git repository URL or None.
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
      git_repo_url (str): git repository URL of the fork.
      branch (str): name of the feature branch of the fork.

    Returns:
      bool: True if the pull was successful.
    """
    command = 'git pull --squash {0:s} {1:s}'.format(git_repo_url, branch)
    exit_code, _, _ = self.RunCommand(command)
    return exit_code == 0

  def PushToOrigin(self, branch, force=False):
    """Forces a push of the active branch of the git repo to origin.

    Args:
      branch (str): name of the feature branch.
      force (Optional[bool]): True if the push should be forced.

    Returns:
      bool: True if the push was successful.
    """
    if force:
      command = 'git push --set-upstream origin {0:s}'.format(branch)
    else:
      command = 'git push -f --set-upstream origin {0:s}'.format(branch)

    exit_code, _, _ = self.RunCommand(command)
    return exit_code == 0

  def RemoveFeatureBranch(self, branch):
    """Removes the git feature branch both local and from origin.

    Args:
      branch (str): name of the feature branch.
    """
    if branch == 'master':
      return

    self.RunCommand('git push origin --delete {0:s}'.format(branch))
    self.RunCommand('git branch -D {0:s}'.format(branch))

  def SynchronizeWithOrigin(self):
    """Synchronizes git with origin.

    Returns:
      bool: True if the git repository has synchronized with origin.
    """
    exit_code, _, _ = self.RunCommand('git fetch origin')
    if exit_code != 0:
      return False

    exit_code, _, _ = self.RunCommand('git pull --no-edit origin master')

    return exit_code == 0

  def SynchronizeWithUpstream(self):
    """Synchronizes git with upstream.

    Returns:
      bool: True if the git repository has synchronized with upstream.
    """
    exit_code, _, _ = self.RunCommand('git fetch upstream')
    if exit_code != 0:
      return False

    exit_code, _, _ = self.RunCommand(
        'git pull --no-edit --rebase upstream master')
    if exit_code != 0:
      return False

    exit_code, _, _ = self.RunCommand('git push')

    return exit_code == 0

  def SwitchToMasterBranch(self):
    """Switches git to the master branch.

    Returns:
      bool: True if the git repository has switched to the master branch.
    """
    exit_code, _, _ = self.RunCommand('git checkout master')
    return exit_code == 0
