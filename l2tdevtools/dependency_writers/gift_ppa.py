# -*- coding: utf-8 -*-
"""Writer for GIFT PPA script files."""

import os

from l2tdevtools.dependency_writers import interface


class GIFTPPAInstallScriptWriter(interface.DependencyFileWriter):
  """GIFT PPA installation script file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'gift_ppa_install.sh')

  # Path to GIFT PPA installation script.
  PATH = os.path.join('config', 'linux', 'gift_ppa_install_py3.sh')

  def _FormatDPKGDebugDependencies(self, debug_dependencies):
    """Formats DPKG debug dependencies for the template.

    Args:
      debug_dependencies (list[str]): DPKG package names of debug dependencies.

    Returns:
      str: formatted DPKG debug dependencies.
    """
    formatted_debug_dependencies = []
    if debug_dependencies:
      for index, dependency in enumerate(sorted(debug_dependencies)):
        if index == 0:
          line = 'DEBUG_DEPENDENCIES="{0:s}'.format(dependency)
        else:
          line = '                    {0:s}'.format(dependency)

        if index + 1 == len(debug_dependencies):
          line = '{0:s}";'.format(line)

        formatted_debug_dependencies.append(line)

    return '\n'.join(formatted_debug_dependencies)

  def _FormatDPKGDevelopmentDependencies(self, development_dependencies):
    """Formats DPKG development dependencies for the template.

    Args:
      development_dependencies (list[str]): DPKG package names of development
          dependencies.

    Returns:
      str: formatted DPKG development dependencies.
    """
    formatted_development_dependencies = []
    if development_dependencies:
      for index, dependency in enumerate(sorted(development_dependencies)):
        if index == 0:
          line = 'DEVELOPMENT_DEPENDENCIES="{0:s}'.format(dependency)
        else:
          line = '                          {0:s}'.format(dependency)

        if index + 1 == len(development_dependencies):
          line = '{0:s}";'.format(line)

        formatted_development_dependencies.append(line)

    return '\n'.join(formatted_development_dependencies)

  def _FormatDPKGPythonDependencies(self, python_dependencies):
    """Formats DPKG Python dependencies for the template.

    Args:
      python_dependencies (list[str]): DPKG package names of Python
          dependencies.

    Returns:
      str: formatted DPKG Python dependencies.
    """
    formatted_python_dependencies = []

    for index, dependency in enumerate(sorted(python_dependencies)):
      if index == 0:
        line = 'PYTHON_DEPENDENCIES="{0:s}'.format(dependency)
      else:
        line = '                     {0:s}'.format(dependency)

      if index + 1 == len(python_dependencies):
        line = '{0:s}";'.format(line)

      formatted_python_dependencies.append(line)

    return '\n'.join(formatted_python_dependencies)

  def _FormatDPKGTestDependencies(self, test_dependencies):
    """Formats DPKG test dependencies for the template.

    Args:
      test_dependencies (list[str]): DPKG package names of test dependencies.

    Returns:
      str: formatted DPKG test dependencies.
    """
    formatted_test_dependencies = []
    if test_dependencies:
      for index, dependency in enumerate(sorted(test_dependencies)):
        if index == 0:
          line = 'TEST_DEPENDENCIES="{0:s}'.format(dependency)
        else:
          line = '                   {0:s}'.format(dependency)

        if index + 1 == len(test_dependencies):
          line = '{0:s}";'.format(line)

        formatted_test_dependencies.append(line)

    return '\n'.join(formatted_test_dependencies)

  def _GetDPKGDebugDependencies(self, python_dependencies):
    """Retrieves DPKG debug dependencies.

    Args:
      python_dependencies (list[str]): DPKG package names of Python
          dependencies.

    Returns:
      list[str]: DPKG package names of Python debug dependencies.
    """
    debug_dependencies = []
    for dependency in sorted(python_dependencies):
      if dependency.startswith('lib') and dependency.endswith('python3'):
        dependency, _, _ = dependency.partition('-')
        debug_dependencies.extend([
            '{0:s}-dbg'.format(dependency),
            '{0:s}-python3-dbg'.format(dependency)])

    return debug_dependencies

  def _Write(self):
    """Writes a gift_ppa_install.sh file."""
    python_dependencies = self._GetDPKGPythonDependencies()
    test_dependencies = self._GetDPKGTestDependencies(python_dependencies)

    # TODO: replace by dev_dependencies.ini or equiv.
    test_dependencies.extend([
        'python3-distutils', 'python3-lib2to3', 'python3-setuptools'])

    # TODO: replace by dev_dependencies.ini or equiv.
    development_dependencies = ['pylint']

    if self._project_definition.name == 'plaso':
      development_dependencies.append('python-sphinx')

    debug_dependencies = self._GetDPKGDebugDependencies(python_dependencies)

    formatted_python_dependencies = self._FormatDPKGPythonDependencies(
        python_dependencies)

    formatted_test_dependencies = self._FormatDPKGTestDependencies(
        test_dependencies)

    formatted_development_dependencies = (
        self._FormatDPKGDevelopmentDependencies(development_dependencies))

    formatted_debug_dependencies = self._FormatDPKGDebugDependencies(
        debug_dependencies)

    template_mappings = {
        'debug_dependencies': formatted_debug_dependencies,
        'development_dependencies': formatted_development_dependencies,
        'project_name': self._project_definition.name,
        'python_dependencies': formatted_python_dependencies,
        'test_dependencies': formatted_test_dependencies}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)

  def Write(self):
    """Writes a gift_ppa_install.sh file."""
    self._Write()
