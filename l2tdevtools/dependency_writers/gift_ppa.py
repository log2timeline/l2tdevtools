# -*- coding: utf-8 -*-
"""Writer for GIFT PPA script files."""

from __future__ import unicode_literals

import abc
import os

from l2tdevtools.dependency_writers import interface


class GIFTPPAInstallScriptWriter(interface.DependencyFileWriter):
  """Shared functionality for GIFT PPA installation script writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'gift_ppa_install.sh')

  # Path to GIFT PPA installation script.
  PATH = ''

  def _Write(self, python_dependencies, python_version=2):
    """Writes a gift_ppa_install.sh file.

    Args:
      python_dependencies (list[str]): list of names of python dependencies.
      python_version (Optional[int]): Python version.
    """
    if python_version == 3:
      python_version_string = 'python3'
    else:
      python_version_string = 'python'

    formatted_python_dependencies = []

    libyal_dependencies = []
    for index, dependency in enumerate(python_dependencies):
      if index == 0:
        line = 'PYTHON{0:d}_DEPENDENCIES="{1:s}'.format(
            python_version, dependency)
      else:
        line = '                      {0:s}'.format(dependency)

      if index + 1 == len(python_dependencies):
        line = '{0:s}";'.format(line)

      formatted_python_dependencies.append(line)

      if dependency.startswith('lib') and dependency.endswith(
          python_version_string):
        dependency, _, _ = dependency.partition('-')
        libyal_dependencies.append(dependency)

    formatted_python_dependencies = '\n'.join(formatted_python_dependencies)

    test_dependencies = ['python-mock']

    development_dependencies = ['python-sphinx', 'pylint']

    debug_dependencies = []
    for index, dependency in enumerate(libyal_dependencies):
      debug_dependencies.append('{0:s}-dbg'.format(dependency))
      debug_dependencies.append(
          '{0:s}-{1:s}-dbg'.format(dependency, python_version_string))

    if python_version == 2 and self._project_definition.name == 'plaso':
      debug_dependencies.append('python-guppy')

    formatted_test_dependencies = []
    if test_dependencies:
      for index, dependency in enumerate(test_dependencies):
        if index == 0:
          line = 'TEST_DEPENDENCIES="{0:s}'.format(dependency)
        else:
          line = '                   {0:s}'.format(dependency)

        if index + 1 == len(test_dependencies):
          line = '{0:s}";'.format(line)

        formatted_test_dependencies.append(line)

    formatted_test_dependencies = '\n'.join(formatted_test_dependencies)

    formatted_development_dependencies = []
    if development_dependencies:
      for index, dependency in enumerate(development_dependencies):
        if index == 0:
          line = 'DEVELOPMENT_DEPENDENCIES="{0:s}'.format(dependency)
        else:
          line = '                          {0:s}'.format(dependency)

        if index + 1 == len(development_dependencies):
          line = '{0:s}";'.format(line)

        formatted_development_dependencies.append(line)

    formatted_development_dependencies = '\n'.join(
        formatted_development_dependencies)

    formatted_debug_dependencies = []
    if debug_dependencies:
      for index, dependency in enumerate(debug_dependencies):
        if index == 0:
          line = 'DEBUG_DEPENDENCIES="{0:s}'.format(dependency)
        else:
          line = '                    {0:s}'.format(dependency)

        if index + 1 == len(debug_dependencies):
          line = '{0:s}";'.format(line)

        formatted_debug_dependencies.append(line)

    formatted_debug_dependencies = '\n'.join(formatted_debug_dependencies)

    pylint_ppa = 'ppa:gift/pylint{0:d}'.format(python_version)

    template_mappings = {
        'debug_dependencies': formatted_debug_dependencies,
        'development_dependencies': formatted_development_dependencies,
        'project_name': self._project_definition.name,
        'pylint_ppa': pylint_ppa,
        'python_dependencies': formatted_python_dependencies,
        'python_version': '{0:d}'.format(python_version),
        'test_dependencies': formatted_test_dependencies}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)

  @abc.abstractmethod
  def Write(self):
    """Writes a gift_ppa_install.sh file."""


class GIFTPPAInstallScriptPY2Writer(GIFTPPAInstallScriptWriter):
  """GIFT PPA installation script file writer for Python 2."""

  PATH = os.path.join('config', 'linux', 'gift_ppa_install.sh')

  def Write(self):
    """Writes a gift_ppa_install.sh file."""
    python2_dependencies = self._dependency_helper.GetDPKGDepends(
        exclude_version=True, python_version=2)
    self._Write(python2_dependencies, python_version=2)


class GIFTPPAInstallScriptPY3Writer(GIFTPPAInstallScriptWriter):
  """GIFT PPA installation script file writer for Python 3."""

  PATH = os.path.join('config', 'linux', 'gift_ppa_install_py3.sh')

  def Write(self):
    """Writes a gift_ppa_install.sh file."""
    python2_dependencies = self._dependency_helper.GetDPKGDepends(
        exclude_version=True, python_version=3)
    self._Write(python2_dependencies, python_version=3)
