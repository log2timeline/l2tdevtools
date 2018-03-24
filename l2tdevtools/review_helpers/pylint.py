# -*- coding: utf-8 -*-
"""Helper for interacting with pylint."""

from __future__ import print_function
from __future__ import unicode_literals

import os
import subprocess

from l2tdevtools.review_helpers import cli


class PylintHelper(cli.CLIHelper):
  """Pylint helper."""

  MINIMUM_VERSION = '1.7.0'

  _MINIMUM_VERSION_TUPLE = MINIMUM_VERSION.split('.')

  _RCFILE_NAME = '.pylintrc'

  def CheckFiles(self, filenames, rcfile):
    """Checks if the linting of the files is correct using pylint.

    Args:
      filenames (list[str]): names of the files to lint.
      rcfile (str): path to the pylint configuration file to use.

    Returns:
      bool: True if the files were linted without errors.
    """
    print('Running linter on changed files.')
    failed_filenames = []
    for filename in filenames:
      print('Checking: {0:s}'.format(filename))

      command = 'pylint --rcfile="{0:s}" {1:s}'.format(rcfile, filename)
      exit_code = subprocess.call(command, shell=True)
      if exit_code != 0:
        failed_filenames.append(filename)

    if failed_filenames:
      print('\nFiles with linter errors:\n{0:s}\n'.format(
          '\n'.join(failed_filenames)))
      return False

    return True

  def CheckUpToDateVersion(self):
    """Checks if the pylint version is up to date.

    Returns:
      bool: True if the pylint version is up to date.
    """
    exit_code, output, _ = self.RunCommand('pylint --version')
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

  def GetRCFile(self, project_path):
    """Gets the path to the pylint configuration file for a project.

    Args:
      project_path (str): path to the root of the project.

    Returns:
      str: absolute path to the pylint configuration file for the project.
    """
    project_file_path = os.path.join(project_path, self._RCFILE_NAME)
    if os.path.exists(project_file_path):
      return os.path.abspath(project_file_path)

    default_path = os.path.join(__file__, '..', '..', '..', self._RCFILE_NAME)
    return os.path.abspath(default_path)
