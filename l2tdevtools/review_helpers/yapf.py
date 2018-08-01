# -*- coding: utf-8 -*-
"""Helper for using yapf (Yet Another Python Formatter)."""
from __future__ import print_function
from __future__ import unicode_literals

import os
import subprocess

from l2tdevtools.review_helpers import cli


class YapfHelper(cli.CLIHelper):
  """yapf helper."""

  MINIMUM_VERSION = '0.22.0'

  _MINIMUM_VERSION_TUPLE = MINIMUM_VERSION.split('.')

  _RCFILE_NAME = '.style.yapf'

  def CheckFiles(self, filenames, rcfile):
    """Checks if the style of the files is correct using yapf.

    Args:
      filenames (list[str]): names of the files to lint.
      rcfile (str): path to the pylint configuration file to use.

    Returns:
      bool: True if the files were checked without errors.
    """
    print('Checking code style with yapf in changed files.')
    failed_filenames = []
    for filename in filenames:
      print('Checking: {0:s}'.format(filename))

      command = 'yapf --style="{0:s}" --diff {1:s}'.format(rcfile, filename)
      exit_code = subprocess.call(command, shell=True)
      if exit_code != 0:
        failed_filenames.append(filename)

    if failed_filenames:
      print(
          '\nFiles with code style problems:\n{0:s}\n'.format(
              '\n'.join(failed_filenames)))
      return False

    return True

  def CheckUpToDateVersion(self):
    """Checks if the yapf version is up to date.

    Returns:
      bool: True if the yapf version is up to date.
    """
    exit_code, output, _ = self.RunCommand('yapf --version')
    if exit_code != 0:
      return False

    version_tuple = (0, 0, 0)
    for line in output.split('\n'):
      if line.startswith('yapf '):
        _, _, version = line.partition(' ')
        # Remove a trailing comma.
        version, _, _ = version.partition(',')

        version_tuple = tuple([int(digit, 10) for digit in version.split('.')])

    return version_tuple >= self._MINIMUM_VERSION_TUPLE

  def GetStyleConfig(self, project_path):
    """Gets the path to the yapf code style file for a project.

    Args:
      project_path (str): path to the root of the project.

    Returns:
      str: absolute path to the yapf code style file for the project, or None
          if there's no code style defined.
    """
    project_file_path = os.path.join(project_path, self._RCFILE_NAME)
    if os.path.exists(project_file_path):
      return os.path.abspath(project_file_path)

    default_path = os.path.join(__file__, '..', '..', '..', self._RCFILE_NAME)
    default_path = os.path.abspath(default_path)
    if os.path.exists(default_path):
      return default_path
    return None
