# -*- coding: utf-8 -*-
"""Writer for GIFT COPR script files."""

import os

from l2tdevtools.dependency_writers import interface


class GIFTCOPRInstallScriptWriter(interface.DependencyFileWriter):
  """GIFT COPR installation script file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'gift_copr_install.sh')

  PATH = os.path.join('config', 'linux', 'gift_copr_install.sh')

  def _FormatRPMDebugDependencies(self, debug_dependencies):
    """Formats RPM debug dependencies for the template.

    Args:
      debug_dependencies (list[str]): RPM package names of debug dependencies.

    Returns:
      str: formatted RPM debug dependencies.
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

  def _FormatRPMDevelopmentDependencies(self, development_dependencies):
    """Formats RPM development dependencies for the template.

    Args:
      development_dependencies (list[str]): RPM package names of development
          dependencies.

    Returns:
      str: formatted RPM development dependencies.
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

  def _FormatRPMPythonDependencies(self, python_dependencies):
    """Formats RPM Python dependencies for the template.

    Args:
      python_dependencies (list[str]): RPM package names of Python dependencies.

    Returns:
      str: formatted RPM Python dependencies.
    """
    formatted_python_dependencies = []

    for index, dependency in enumerate(sorted(python_dependencies)):
      if index == 0:
        line = 'PYTHON3_DEPENDENCIES="{0:s}'.format(dependency)
      else:
        line = '                      {0:s}'.format(dependency)

      if index + 1 == len(python_dependencies):
        line = '{0:s}";'.format(line)

      formatted_python_dependencies.append(line)

    return '\n'.join(formatted_python_dependencies)

  def _FormatRPMTestDependencies(self, test_dependencies):
    """Formats RPM test dependencies for the template.

    Args:
      test_dependencies (list[str]): RPM package names of test dependencies.

    Returns:
      str: formatted RPM test dependencies.
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

  def _GetRPMDebugDependencies(self, python_dependencies):
    """Retrieves RPM debug dependencies.

    Args:
      python_dependencies (list[str]): RPM package names of Python dependencies.

    Returns:
      list[str]: RPM package names of Python debug dependencies.
    """
    debug_dependencies = []
    for dependency in sorted(python_dependencies):
      if dependency.startswith('lib') and (
          dependency.endswith('python') or dependency.endswith('python2') or
          dependency.endswith('python3')):
        libyal_dependency, _, _ = dependency.partition('-')
        debug_dependencies.extend([
            '{0:s}-debuginfo'.format(libyal_dependency),
            '{0:s}-debuginfo'.format(dependency)])

    return debug_dependencies

  def Write(self):
    """Writes a gift_copr_install.sh file."""
    python_dependencies = self._GetRPMPythonDependencies()
    test_dependencies = self._GetRPMTestDependencies(python_dependencies)

    # TODO: replace by dev_dependencies.ini or equiv.
    development_dependencies = ['pylint']

    if self._project_definition.name == 'plaso':
      development_dependencies.append('python-sphinx')

    debug_dependencies = self._GetRPMDebugDependencies(python_dependencies)

    formatted_python_dependencies = self._FormatRPMPythonDependencies(
        python_dependencies)

    formatted_test_dependencies = self._FormatRPMTestDependencies(
        test_dependencies)

    formatted_development_dependencies = self._FormatRPMDevelopmentDependencies(
        development_dependencies)

    formatted_debug_dependencies = self._FormatRPMDebugDependencies(
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
