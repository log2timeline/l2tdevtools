# -*- coding: utf-8 -*-
"""Writers for Travis-CI script files."""

from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class TravisInstallScriptWriter(interface.DependencyFileWriter):
  """Travis-CI install.sh file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'install.sh')

  PATH = os.path.join('config', 'travis', 'install.sh')

  _URL_L2TDEVTOOLS = 'https://github.com/log2timeline/l2tdevtools.git'

  def Write(self):
    """Writes an install.sh file."""
    l2tbinaries_dependencies = self._dependency_helper.GetL2TBinaries(
        platform='macos')

    l2tbinaries_test_dependencies = ['funcsigs', 'mock', 'pbr']
    if 'six' not in l2tbinaries_dependencies:
      l2tbinaries_test_dependencies.append('six')

    if self._project_definition.name == 'artifacts':
      l2tbinaries_test_dependencies.append('yapf')

    python2_dependencies = self._dependency_helper.GetDPKGDepends(
        exclude_version=True, python_version=2)

    python2_test_dependencies = ['python-coverage', 'python-mock', 'python-tox']
    if self._project_definition.name == 'artifacts':
      # Note that the artifacts tests will use the Python 2 version of yapf.
      python2_test_dependencies.append('python-yapf')
      python2_test_dependencies.append('yapf')

    python3_dependencies = self._dependency_helper.GetDPKGDepends(
        exclude_version=True, python_version=3)

    python3_test_dependencies = [
        'python3-mock', 'python3-setuptools', 'python3-tox']
    if self._project_definition.name == 'artifacts':
      # Note that the artifacts tests will use the Python 2 version of yapf.
      python3_test_dependencies.append('python-yapf')
      python3_test_dependencies.append('yapf')

    template_mappings = {
        'l2tbinaries_dependencies': ' '.join(l2tbinaries_dependencies),
        'l2tbinaries_test_dependencies': ' '.join(sorted(
            l2tbinaries_test_dependencies)),
        'python2_dependencies': ' '.join(python2_dependencies),
        'python2_test_dependencies': ' '.join(sorted(
            python2_test_dependencies)),
        'python3_dependencies': ' '.join(python3_dependencies),
        'python3_test_dependencies': ' '.join(sorted(
            python3_test_dependencies)),
    }

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class TravisRunTestsScriptWriter(interface.DependencyFileWriter):
  """Travis-CI runtests.sh file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'runtests.sh')

  PATH = os.path.join('config', 'travis', 'runtests.sh')

  def Write(self):
    """Writes a runtests.sh file."""
    paths_to_lint = [self._project_definition.name]
    for path_to_lint in ('config', 'scripts', 'tests', 'tools'):
      if os.path.isdir(path_to_lint):
        paths_to_lint.append(path_to_lint)

    paths_to_lint = sorted(paths_to_lint)
    if os.path.isfile('setup.py'):
      paths_to_lint.insert(0, 'setup.py')

    template_mappings = {
        'project_name': self._project_definition.name,
        'paths_to_lint': ' '.join(paths_to_lint)
    }

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class TravisRunWithTimeoutScriptWriter(interface.DependencyFileWriter):
  """Travis-CI run_with_timeout.sh file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'run_with_timeout.sh')

  PATH = os.path.join('config', 'travis', 'run_with_timeout.sh')

  def Write(self):
    """Writes a run_with_timeout.sh file."""
    template_mappings = {}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
