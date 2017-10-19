# -*- coding: utf-8 -*-
"""Helper for interacting with sphinx-apidoc."""
from __future__ import print_function
from __future__ import unicode_literals

from l2tdevtools.helpers import cli


class SphinxAPIDocHelper(cli.CLIHelper):
  """Sphinx-apidoc helper functions."""

  _MINIMUM_VERSION_TUPLE = (1, 2, 0)

  def __init__(self, project):
    """Initializes a sphinx-apidoc helper.

    Args:
      project (str): github project name.
    """
    super(SphinxAPIDocHelper, self).__init__()
    self._project = project

  def CheckUpToDateVersion(self):
    """Checks if the sphinx-apidoc version is up to date.

    Returns:
      bool: True if the sphinx-apidoc version is up to date.
    """
    exit_code, output, _ = self.RunCommand('sphinx-apidoc --version')
    if exit_code != 0:
      return False

    version_tuple = (0, 0, 0)
    for line in output.split(b'\n'):
      if line.startswith(b'Sphinx (sphinx-apidoc) '):
        _, _, version = line.rpartition(b' ')

        version_tuple = tuple([int(digit) for digit in version.split(b'.')])

    return version_tuple >= self._MINIMUM_VERSION_TUPLE

  def UpdateAPIDocs(self):
    """Updates the API docs.

    Returns:
      bool: True if the API docs have been updated.
    """
    command = 'sphinx-apidoc -f -o docs {0:s}'.format(self._project)
    exit_code, output, _ = self.RunCommand(command)
    print(output)

    return exit_code == 0
