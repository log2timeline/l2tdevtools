# -*- coding: utf-8 -*-
"""Helper for interacting with a project."""

from __future__ import unicode_literals

import logging
import os
import random
import time

from l2tdevtools import project_config
from l2tdevtools.review_helpers import cli


class ProjectHelper(cli.CLIHelper):
  """Helper for interacting with a project.

  Attributes:
    project_name (str): name of the project.
  """

  _AUTHORS_FILE_HEADER = [
      '# Names should be added to this file with this pattern:',
      '#',
      '# For individuals:',
      '#   Name (email address)',
      '#',
      '# For organizations:',
      '#   Organization (fnmatch pattern)',
      '#',
      '# See python fnmatch module documentation for more information.',
      '',
      'Google Inc. (*@google.com)'] # yapf: disable

  # yapf: disable

  _REVIEWERS_PER_PROJECT = {
      'dfdatetime': frozenset([
          'joachimmetz',
          'Onager']),
      'dfkinds': frozenset([
          'joachimmetz',
          'Onager']),
      'dfvfs': frozenset([
          'joachimmetz',
          'Onager']),
      'dfwinreg': frozenset([
          'joachimmetz',
          'Onager']),
      'dftimewolf': frozenset([
          'Onager',
          'someguyiknow',
          'tomchop']),
      'l2tpreg': frozenset([
          'joachimmetz',
          'Onager']),
      'plaso': frozenset([
          'joachimmetz',
          'Onager',
          'rgayon']),
      'PlasoScaffolder': frozenset([
          'joachimmetz',
          'Onager'])}

  _REVIEWERS_DEFAULT = frozenset([
      'joachimmetz',
      'Onager'])

  # yapf: enable

  # Note that review is submodule name of l2tdevtools not a stand-alone project.
  SUPPORTED_PROJECTS = frozenset([
      'acstore', 'artifacts', 'dfdatetime', 'dfkinds', 'dfvfs', 'dfwinreg',
      'dftimewolf', 'dtfabric', 'dtformats', 'esedb-kb', 'l2tdevtools',
      'l2tdocs', 'l2tpreg', 'plaso', 'PlasoScaffolder', 'review', 'vstools',
      'winevt-kb', 'winreg-kb'])

  def __init__(self, project_path):
    """Initializes a project helper.

    Args:
      project_path (str): path to the project.

    Raises:
      ValueError: if the project name is not supported.
    """
    super(ProjectHelper, self).__init__()
    self._project_definition = None
    self.project_name = self._GetProjectName(project_path)

  @property
  def version_file_path(self):
    """str: path of the version file."""
    return os.path.join(self.project_name, '__init__.py')

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
    project_name = os.path.basename(project_name)

    for supported_project_name in self.SUPPORTED_PROJECTS:
      if supported_project_name in project_name:
        return supported_project_name

    raise ValueError('Unsupported project name: {0:s}.'.format(project_name))

  def _ReadFileContents(self, path):
    """Reads the contents of a file.

    Args:
      path (str): path of the file.

    Returns:
      bytes: file content or None if not available.
    """
    if not os.path.exists(path):
      logging.error('Missing file: {0:s}'.format(path))
      return None

    try:
      with open(path, 'rb') as file_object:
        file_contents = file_object.read()

    except IOError as exception:
      logging.error('Unable to read file with error: {0!s}'.format(exception))
      return None

    try:
      file_contents = file_contents.decode('utf-8')
    except UnicodeDecodeError as exception:
      logging.error('Unable to read file with error: {0!s}'.format(exception))
      return None

    return file_contents

  @classmethod
  def GetReviewer(cls, project_name, author):
    """Determines the GitHub username of the reviewer.

    Args:
      project_name (str): name of the project.
      author (str): GitHub username of the author.

    Returns:
      str: GitHub username of the reviewer.
    """
    reviewers = list(
        cls._REVIEWERS_PER_PROJECT.get(project_name, cls._REVIEWERS_DEFAULT))

    try:
      reviewers.remove(author)
    except ValueError:
      pass

    random.shuffle(reviewers)

    return reviewers[0]

  def GetVersion(self):
    """Retrieves the project version from the version file.

    Returns:
      str: project version or None if not available.
    """
    version_file_contents = self._ReadFileContents(self.version_file_path)
    if not version_file_contents:
      return None

    # The version is formatted as:
    # __version__ = 'VERSION'
    version_line_prefix = '__version__ = \''

    lines = version_file_contents.split('\n')
    for line in lines:
      if line.startswith(version_line_prefix):
        return line[len(version_line_prefix):-1]

    return None

  def ReadDefinitionFile(self):
    """Reads the project definitions file (project_name.ini).

    Returns:
      ProjectDefinition: project definition.
    """
    if self._project_definition is None:
      project_file = '{0:s}.ini'.format(self.project_name)

      project_reader = project_config.ProjectDefinitionReader()
      with open(project_file, 'r') as file_object:
        self._project_definition = project_reader.Read(file_object)

    return self._project_definition

  def UpdateAuthorsFile(self):
    """Updates the AUTHORS file.

    Returns:
      bool: True if the AUTHORS file update was successful.
    """
    exit_code, output, _ = self.RunCommand('git log --format="%aN (%aE)"')
    if exit_code != 0:
      return False

    lines = output.split(b'\n')

    # Reverse the lines since we want the oldest commits first.
    lines.reverse()

    authors_by_commit = []
    authors = {}
    for author in lines:
      name, _, email_address = author[:-1].rpartition('(')
      if email_address in authors:
        if name != authors[email_address]:
          logging.warning(
              'Detected name mismatch for author: {0:d}.'.format(
                  email_address))
        continue

      authors[email_address] = name
      authors_by_commit.append(author)

    file_content = []
    file_content.extend(self._AUTHORS_FILE_HEADER)
    file_content.extend(authors_by_commit)

    file_content = '\n'.join(file_content)
    file_content = file_content.encode('utf-8')

    with open('AUTHORS', 'wb') as file_object:
      file_object.write(file_content)

    return True

  def UpdateDpkgChangelogFile(self):
    """Updates the dpkg changelog file.

    Returns:
      bool: True if the dpkg changelog file was updated or if the dpkg
          changelog file does not exist.
    """
    project_definition = self.ReadDefinitionFile()

    project_version = self.GetVersion()

    dpkg_changelog_path = os.path.join('config', 'dpkg', 'changelog')
    if not os.path.exists(dpkg_changelog_path):
      return True

    dpkg_maintainter = project_definition.maintainer
    if not dpkg_maintainter:
      dpkg_maintainter = 'Log2Timeline <log2timeline-dev@googlegroups.com>'

    dpkg_date = time.strftime('%a, %d %b %Y %H:%M:%S %z')
    dpkg_changelog_content = '\n'.join([
        '{0:s} ({1:s}-1) unstable; urgency=low'.format(
            self.project_name, project_version),
        '',
        '  * Auto-generated',
        '',
        ' -- {0:s}  {1:s}'.format(dpkg_maintainter, dpkg_date)]) #yapf: disable

    try:
      dpkg_changelog_content = dpkg_changelog_content.encode('utf-8')
    except UnicodeEncodeError as exception:
      logging.error(
          'Unable to write dpkg changelog file with error: {0!s}'.format(
              exception))
      return False

    try:
      with open(dpkg_changelog_path, 'wb') as file_object:
        file_object.write(dpkg_changelog_content)
    except IOError as exception:
      logging.error(
          'Unable to write dpkg changelog file with error: {0!s}'.format(
              exception))
      return False

    return True

  def UpdateVersionFile(self):
    """Updates the version file.

    Returns:
      bool: True if the file was updated.
    """
    version_file_contents = self._ReadFileContents(self.version_file_path)
    if not version_file_contents:
      logging.error('Unable to read version file.')
      return False

    date_version = time.strftime('%Y%m%d')
    lines = version_file_contents.split('\n')
    for line_index, line in enumerate(lines):
      if line.startswith('__version__ = '):
        version_string = '__version__ = \'{0:s}\''.format(date_version)
        lines[line_index] = version_string

    version_file_contents = '\n'.join(lines)

    try:
      version_file_contents = version_file_contents.encode('utf-8')
    except UnicodeEncodeError as exception:
      logging.error(
          'Unable to write version file with error: {0!s}'.format(exception))
      return False

    try:
      with open(self.version_file_path, 'wb') as file_object:
        file_object.write(version_file_contents)

    except IOError as exception:
      logging.error(
          'Unable to write version file with error: {0!s}'.format(exception))
      return False

    return True
