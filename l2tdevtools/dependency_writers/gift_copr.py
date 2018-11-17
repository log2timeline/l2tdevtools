# -*- coding: utf-8 -*-
"""Writer for GIFT COPR script files."""

from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class GIFTCOPRInstallScriptWriter(interface.DependencyFileWriter):
  """GIFT COPR installation script file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'gift_copr_install.sh')

  PATH = os.path.join('config', 'linux', 'gift_copr_install.sh')

  def Write(self):
    """Writes a gift_copr_install.sh file."""
    python_version = 2

    python_dependencies = self._dependency_helper.GetRPMRequires(
        exclude_version=True, python_version=python_version)

    formatted_python_dependencies = []

    pyyal_dependencies = []
    for index, dependency in enumerate(sorted(python_dependencies)):
      if index == 0:
        line = 'PYTHON{0:d}_DEPENDENCIES="{1:s}'.format(
            python_version, dependency)
      else:
        line = '                      {0:s}'.format(dependency)

      if index + 1 == len(python_dependencies):
        line = '{0:s}";'.format(line)

      formatted_python_dependencies.append(line)

      if dependency.startswith('lib') and (
          dependency.endswith('python') or dependency.endswith('python2') or
          dependency.endswith('python3')):
        pyyal_dependencies.append(dependency)

    formatted_python_dependencies = '\n'.join(formatted_python_dependencies)

    test_dependencies = self._test_dependency_helper.GetRPMRequires(
        exclude_version=True, python_version=python_version)

    # TODO: replace by dev_dependencies.ini or equiv.
    development_dependencies = ['pylint']

    if self._project_definition.name == 'plaso':
      development_dependencies.append('python-sphinx')

    debug_dependencies = []
    for pyyal_dependency in sorted(pyyal_dependencies):
      libyal_dependency, _, _ = pyyal_dependency.partition('-')
      debug_dependencies.extend([
          '{0:s}-debuginfo'.format(libyal_dependency),
          '{0:s}-debuginfo'.format(pyyal_dependency)])

    if python_version == 2 and self._project_definition.name == 'plaso':
      debug_dependencies.append('python-guppy')

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

    formatted_test_dependencies = '\n'.join(formatted_test_dependencies)

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

    formatted_development_dependencies = '\n'.join(
        formatted_development_dependencies)

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

    formatted_debug_dependencies = '\n'.join(formatted_debug_dependencies)

    template_mappings = {
        'debug_dependencies': formatted_debug_dependencies,
        'development_dependencies': formatted_development_dependencies,
        'project_name': self._project_definition.name,
        'python_dependencies': formatted_python_dependencies,
        'python_version': '{0:d}'.format(python_version),
        'test_dependencies': formatted_test_dependencies}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
