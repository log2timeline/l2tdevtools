# -*- coding: utf-8 -*-
"""Helper for interacting with a project."""

import logging
import os
import random

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
      'Google Inc. (*@google.com)']

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
      'plaso': frozenset([
          'joachimmetz',
          'Onager',
          'rgayon']),
      'l2tscaffolder': frozenset([
          'kiddinn',
          'Onager'])}

  _REVIEWERS_DEFAULT = frozenset([
      'joachimmetz',
      'Onager'])

  SUPPORTED_PROJECTS = frozenset([
      'acstore',
      'artifacts',
      'clitooltester',
      'dfdatetime',
      'dfkinds',
      'dftimewolf',
      'dfvfs',
      'dfvfs-snippets',
      'dfwinreg',
      'dtfabric',
      'dtformats',
      'esedb-kb',
      'l2tdevtools',
      'l2tdocs',
      'l2tscaffolder',
      'olecf-kb',
      'plaso',
      'timesketch',
      'turbinia',
      'vstools',
      'winevt-kb',
      'winreg-kb'])

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

    # The review.py check is needed for the l2tdevtools tests.
    if (project_name != 'review.py' and
        project_name not in self.SUPPORTED_PROJECTS):
      raise ValueError('Unsupported project name: {0:s}.'.format(project_name))

    return project_name

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
