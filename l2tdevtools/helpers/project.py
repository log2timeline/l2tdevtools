# -*- coding: utf-8 -*-
"""Helper for interacting with projects."""
import logging
import os
import time

from l2tdevtools.helpers import cli


class ProjectHelper(cli.CLIHelper):
  """Helper for interacting with projects.

  Attributes:
    project_name (str): name of the project.
  """


  _AUTHORS_FILE_HEADER = [
      u'# Names should be added to this file with this pattern:',
      u'#',
      u'# For individuals:',
      u'#   Name (email address)',
      u'#',
      u'# For organizations:',
      u'#   Organization (fnmatch pattern)',
      u'#',
      u'# See python fnmatch module documentation for more information.',
      u'',
      u'Google Inc. (*@google.com)'] # yapf: disable

  SUPPORTED_PROJECTS = frozenset([
      u'artifacts', u'dfdatetime', u'dfkinds', u'dfvfs', u'dfwinreg',
      u'dftimewolf', u'eccemotus', u'l2tdevtools', u'l2tdocs', u'l2tpreg',
      u'review', u'plaso'])

  def __init__(self, project_path):
    """Initializes a project helper.

    Args:
      project_path (str): path to the project.

    Raises:
      ValueError: if the project name is not supported.
    """
    super(ProjectHelper, self).__init__()
    self.project_name = self._GetProjectName(project_path)

  @property
  def version_file_path(self):
    """str: path of the version file."""
    return os.path.join(self.project_name, u'__init__.py')

  def _GetProjectName(self, project_path):
    """Retrieves the project name from the script path.

    Args:
      project_path (str): path to the root of the project.

    Returns:
      str: project name.

    Raises:
      ValueError: if the project name is not supported.
    """
    project_name = os.path.abspath(project_path)
    project_name = os.path.dirname(project_name)
    project_name = os.path.dirname(project_name)
    project_name = os.path.basename(project_name)

    for supported_project_name in self.SUPPORTED_PROJECTS:
      if supported_project_name in project_name:
        return supported_project_name

    raise ValueError(u'Unsupported project name: {0:s}.'.format(project_name))

  def _ReadFileContents(self, path):
    """Reads the contents of a file.

    Args:
      path (str): path of the file.

    Returns:
      bytes: file content or None.
    """
    if not os.path.exists(path):
      logging.error(u'Missing file: {0:s}'.format(path))
      return

    try:
      with open(path, u'rb') as file_object:
        file_contents = file_object.read()

    except IOError as exception:
      logging.error(u'Unable to read file with error: {0!s}'.format(exception))
      return

    try:
      file_contents = file_contents.decode(u'utf-8')
    except UnicodeDecodeError as exception:
      logging.error(u'Unable to read file with error: {0!s}'.format(exception))
      return

    return file_contents

  def GetVersion(self):
    """Retrieves the project version from the version file.

    Returns:
      str: project version or None.
    """
    version_file_contents = self._ReadFileContents(self.version_file_path)
    if not version_file_contents:
      return

    # The version is formatted as:
    # __version__ = 'VERSION'
    version_line_prefix = u'__version__ = \''

    lines = version_file_contents.split(u'\n')
    for line in lines:
      if line.startswith(version_line_prefix):
        return line[len(version_line_prefix):-1]

    return

  def UpdateDpkgChangelogFile(self):
    """Updates the dpkg changelog file.

    Returns:
      bool: True if the dpkg changelog file was updated or if the dpkg
          changelog file does not exists.
    """
    project_version = self.GetVersion()

    dpkg_changelog_path = os.path.join(u'config', u'dpkg', u'changelog')
    if not os.path.exists(dpkg_changelog_path):
      return True

    dpkg_maintainter = u'Log2Timeline <log2timeline-dev@googlegroups.com>'
    dpkg_date = time.strftime(u'%a, %d %b %Y %H:%M:%S %z')
    dpkg_changelog_content = u'\n'.join([
        u'{0:s} ({1:s}-1) unstable; urgency=low'.format(
            self.project_name, project_version),
        u'',
        u'  * Auto-generated',
        u'',
        u' -- {0:s}  {1:s}'.format(dpkg_maintainter, dpkg_date)]) #yapf: disable

    try:
      dpkg_changelog_content = dpkg_changelog_content.encode(u'utf-8')
    except UnicodeEncodeError as exception:
      logging.error(
          u'Unable to write dpkg changelog file with error: {0!s}'.format(
              exception))
      return False

    try:
      with open(dpkg_changelog_path, u'wb') as file_object:
        file_object.write(dpkg_changelog_content)
    except IOError as exception:
      logging.error(
          u'Unable to write dpkg changelog file with error: {0!s}'.format(
              exception))
      return False

    return True

  def UpdateAuthorsFile(self):
    """Updates the AUTHORS file.

    Returns:
      bool: True if the AUTHORS file update was successful.
    """
    exit_code, output, _ = self.RunCommand(u'git log --format="%aN (%aE)"')
    if exit_code != 0:
      return False

    lines = output.split(b'\n')

    # Reverse the lines since we want the oldest commits first.
    lines.reverse()

    authors_by_commit = []
    authors = {}
    for author in lines:
      name, _, email_address = author[:-1].rpartition(u'(')
      if email_address in authors:
        if name != authors[email_address]:
          logging.warning(
              u'Detected name mismatch for author: {0:d}.'.format(
                  email_address))
        continue

      authors[email_address] = name
      authors_by_commit.append(author)

    file_content = []
    file_content.extend(self._AUTHORS_FILE_HEADER)
    file_content.extend(authors_by_commit)

    file_content = u'\n'.join(file_content)
    file_content = file_content.encode(u'utf-8')

    with open(u'AUTHORS', 'wb') as file_object:
      file_object.write(file_content)

    return True

  def UpdateVersionFile(self):
    """Updates the version file.

    Returns:
      bool: True if the file was updated.
    """
    version_file_contents = self._ReadFileContents(self.version_file_path)
    if not version_file_contents:
      logging.error(u'Unable to read version file.')
      return False

    date_version = time.strftime(u'%Y%m%d')
    lines = version_file_contents.split(u'\n')
    for line_index, line in enumerate(lines):
      if line.startswith(u'__version__ = '):
        version_string = u'__version__ = \'{0:s}\''.format(date_version)
        lines[line_index] = version_string

    version_file_contents = u'\n'.join(lines)

    try:
      version_file_contents = version_file_contents.encode(u'utf-8')
    except UnicodeEncodeError as exception:
      logging.error(
          u'Unable to write version file with error: {0!s}'.format(exception))
      return False

    try:
      with open(self.version_file_path, u'wb') as file_object:
        file_object.write(version_file_contents)

    except IOError as exception:
      logging.error(
          u'Unable to write version file with error: {0!s}'.format(exception))
      return False

    return True
