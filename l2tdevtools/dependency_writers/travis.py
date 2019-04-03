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

    l2tbinaries_test_dependencies = self._test_dependency_helper.GetL2TBinaries(
        platform='macos')

    l2tbinaries_test_dependencies = sorted(l2tbinaries_test_dependencies)

    dpkg_python2_dependencies = self._GetDPKGPythonDependencies(
        python_version=2)

    dpkg_python2_test_dependencies = self._GetDPKGTestDependencies(
        dpkg_python2_dependencies, python_version=2)

    dpkg_python3_dependencies = self._GetDPKGPythonDependencies(
        python_version=3)

    dpkg_python3_test_dependencies = self._GetDPKGTestDependencies(
        dpkg_python3_dependencies, python_version=3)

    rpm_python2_dependencies = self._GetRPMPythonDependencies(python_version=2)

    rpm_python2_test_dependencies = self._GetRPMTestDependencies(
        rpm_python2_dependencies, python_version=2)

    rpm_python3_dependencies = self._GetRPMPythonDependencies(python_version=3)

    rpm_python3_test_dependencies = self._GetRPMTestDependencies(
        rpm_python3_dependencies, python_version=3)

    template_mappings = {
        'l2tbinaries_dependencies': ' '.join(l2tbinaries_dependencies),
        'l2tbinaries_test_dependencies': ' '.join(
            l2tbinaries_test_dependencies),
        'dpkg_python2_dependencies': ' '.join(dpkg_python2_dependencies),
        'dpkg_python2_test_dependencies': ' '.join(
            dpkg_python2_test_dependencies),
        'dpkg_python3_dependencies': ' '.join(dpkg_python3_dependencies),
        'dpkg_python3_test_dependencies': ' '.join(
            dpkg_python3_test_dependencies),
        'project_name': self._project_definition.name,
        'rpm_python2_dependencies': ' '.join(rpm_python2_dependencies),
        'rpm_python2_test_dependencies': ' '.join(
            rpm_python2_test_dependencies),
        'rpm_python3_dependencies': ' '.join(rpm_python3_dependencies),
        'rpm_python3_test_dependencies': ' '.join(
            rpm_python3_test_dependencies)}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class TravisRunPylintScriptWriter(interface.DependencyFileWriter):
  """Travis-CI run_pylint.sh file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'run_pylint.sh')

  PATH = os.path.join('config', 'travis', 'run_pylint.sh')

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
        'paths_to_lint': ' '.join(paths_to_lint)
    }

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class TravisRunTestsScriptWriter(interface.DependencyFileWriter):
  """Travis-CI runtests.sh file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'runtests.sh')

  PATH = os.path.join('config', 'travis', 'runtests.sh')

  def Write(self):
    """Writes a runtests.sh file."""
    template_mappings = {
        'project_name': self._project_definition.name,
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
