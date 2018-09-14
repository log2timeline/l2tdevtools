# -*- coding: utf-8 -*-
"""Writer for GIFT PPA script files."""

from __future__ import unicode_literals

import abc
import os

from l2tdevtools.dependency_writers import interface

class GIFTPPAInstallScriptWriter(interface.DependencyFileWriter):
  """Shared functionality for GIFT PPA installation script writer."""

  # Path to GIFT PPA installation script.
  PATH = ''

  _FILE_HEADER = [
      '#!/usr/bin/env bash',
      '#',
      ('# This file is generated by l2tdevtools update-dependencies.py any '
       'dependency'),
      '# related changes should be made in dependencies.ini.',
      '',
      '# Exit on error.',
      'set -e',
      '',
      ('# Dependencies for running {project_name:s}, alphabetized, one per '
       'line.'),
      ('# This should not include packages only required for testing or '
       'development.')] # yapf: disable

  _ADDITIONAL_DEPENDENCIES = [
      '',
      ('# Additional dependencies for running {project_name:s} tests, '
       'alphabetized,'),
      '# one per line.',
      'TEST_DEPENDENCIES="python-mock";',
      '',
      ('# Additional dependencies for doing {project_name:s} development, '
       'alphabetized,'),
      '# one per line.',
      'DEVELOPMENT_DEPENDENCIES="python-sphinx',
      '                          pylint";']  # yapf: disable

  _DEBUG_DEPENDENCIES = [
      '',
      ('# Additional dependencies for doing {project_name:s} debugging, '
       'alphabetized,'),
      '# one per line.']  # yapf: disable

  _FILE_FOOTER = []

  _FILE_FOOTER_DEBUG_DEPENDENCIES = [
      '',
      'if [[ "$*" =~ "include-debug" ]]; then',
      '    sudo apt-get install -y ${{DEBUG_DEPENDENCIES}}',
      'fi']  # yapf: disable

  _FILE_FOOTER_DEVELOPMENT_DEPENDENCIES = [
      '',
      'if [[ "$*" =~ "include-development" ]]; then',
      '    sudo apt-get install -y ${{DEVELOPMENT_DEPENDENCIES}}',
      'fi']  # yapf: disable

  _FILE_FOOTER_TEST_DEPENDENCIES = [
      '',
      'if [[ "$*" =~ "include-test" ]]; then',
      '    sudo apt-get install -y ${{TEST_DEPENDENCIES}}',
      'fi',
      '']  # yapf: disable

  def _Write(self, python_dependencies, python_version=2):
    """Writes a gift_ppa_install.sh file.

    Args:
      python_dependencies (list[str]): list of names of python dependencies.
      python_version (Optional[int]): Python version.
    """
    file_content = []
    file_content.extend(self._FILE_HEADER)

    if python_version == 3:
      python_version_string = 'python3'
    else:
      python_version_string = 'python'

    libyal_dependencies = []
    for index, dependency in enumerate(python_dependencies):
      if index == 0:
        file_content.append('PYTHON{0:d}_DEPENDENCIES="{1:s}'.format(
            python_version, dependency))
      elif index + 1 == len(python_dependencies):
        file_content.append('                      {0:s}";'.format(dependency))
      else:
        file_content.append('                      {0:s}'.format(dependency))


      if dependency.startswith('lib') and dependency.endswith(
          python_version_string):
        dependency, _, _ = dependency.partition('-')
        libyal_dependencies.append(dependency)

    file_content.extend(self._ADDITIONAL_DEPENDENCIES)

    debug_dependencies = []
    for index, dependency in enumerate(libyal_dependencies):
      debug_dependencies.append('{0:s}-dbg'.format(dependency))
      debug_dependencies.append(
          '{0:s}-{1:s}-dbg'.format(dependency, python_version_string))


    if (python_version == 2  and
        self._project_definition.name == 'plaso'):
      debug_dependencies.append('python-guppy')

    if debug_dependencies:
      file_content.extend(self._DEBUG_DEPENDENCIES)

      for index, dependency in enumerate(debug_dependencies):
        if index == 0:
          file_content.append('DEBUG_DEPENDENCIES="{0:s}'.format(dependency))
        elif index + 1 == len(debug_dependencies):
          file_content.append('                    {0:s}";'.format(dependency))
        else:
          file_content.append('                    {0:s}'.format(dependency))

    file_content.extend(self._FILE_FOOTER)

    if debug_dependencies:
      file_content.extend(self._FILE_FOOTER_DEBUG_DEPENDENCIES)

    file_content.extend(self._FILE_FOOTER_DEVELOPMENT_DEPENDENCIES)
    file_content.extend(self._FILE_FOOTER_TEST_DEPENDENCIES)

    template_mappings = {'project_name': self._project_definition.name}

    file_content = '\n'.join(file_content)
    file_content = file_content.format(**template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)

  @abc.abstractmethod
  def Write(self):
    """Writes a gift_ppa_install.sh file."""


class GIFTPPAInstallScriptPY2Writer(GIFTPPAInstallScriptWriter):
  """GIFT PPA installation script file writer for Python 2."""

  PATH = os.path.join('config', 'linux', 'gift_ppa_install.sh')

  _FILE_FOOTER = [
      '',
      'sudo add-apt-repository ppa:gift/dev -y',
      'sudo apt-get update -q',
      'sudo apt-get install -y ${{PYTHON2_DEPENDENCIES}}']  # yapf: disable

  def Write(self):
    """Writes a gift_ppa_install.sh file."""
    python2_dependencies = self._dependency_helper.GetDPKGDepends(
        exclude_version=True, python_version=2)
    self._Write(python2_dependencies, python_version=2)


class GIFTPPAInstallScriptPY3Writer(GIFTPPAInstallScriptWriter):
  """GIFT PPA installation script file writer for Python 3."""

  PATH = os.path.join('config', 'linux', 'gift_ppa_install_py3.sh')

  _FILE_FOOTER = [
      '',
      'sudo add-apt-repository ppa:gift/dev -y',
      'sudo apt-get update -q',
      'sudo apt-get install -y ${{PYTHON3_DEPENDENCIES}}']  # yapf: disable

  def Write(self):
    """Writes a gift_ppa_install.sh file."""
    python2_dependencies = self._dependency_helper.GetDPKGDepends(
        exclude_version=True, python_version=3)
    self._Write(python2_dependencies, python_version=3)
