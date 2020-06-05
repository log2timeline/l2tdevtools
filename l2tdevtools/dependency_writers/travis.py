# -*- coding: utf-8 -*-
"""Writers for Travis-CI script files."""

from __future__ import unicode_literals

import io
import os

from l2tdevtools.dependency_writers import interface


class TravisInstallScriptWriter(interface.DependencyFileWriter):
  """Travis-CI install.sh file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'travis', 'install.sh')

  PATH = os.path.join('config', 'travis', 'install.sh')

  _URL_L2TDEVTOOLS = 'https://github.com/log2timeline/l2tdevtools.git'

  def Write(self):
    """Writes an install.sh file."""
    dpkg_build_dependencies = ['build-essential']

    dpkg_python3_dependencies = self._GetDPKGPythonDependencies(
        python_version=3)

    dpkg_python3_test_dependencies = self._GetDPKGTestDependencies(
        dpkg_python3_dependencies, python_version=3)

    rpm_python3_dependencies = self._GetRPMPythonDependencies(python_version=3)

    rpm_python3_test_dependencies = self._GetRPMTestDependencies(
        rpm_python3_dependencies, python_version=3)

    template_mappings = {
        'dpkg_build_dependencies': ' '.join(dpkg_build_dependencies),
        'dpkg_python3_dependencies': ' '.join(dpkg_python3_dependencies),
        'dpkg_python3_test_dependencies': ' '.join(
            dpkg_python3_test_dependencies),
        'project_name': self._project_definition.name,
        'rpm_python3_dependencies': ' '.join(rpm_python3_dependencies),
        'rpm_python3_test_dependencies': ' '.join(
            rpm_python3_test_dependencies)}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)


class TravisRunCoverageScriptWriter(interface.DependencyFileWriter):
  """Travis-CI run_coverage.sh file writer."""

  _TEMPLATE_FILE = os.path.join(
      'data', 'templates', 'travis', 'run_coverage.sh')

  PATH = os.path.join('config', 'travis', 'run_coverage.sh')

  def Write(self):
    """Writes a runtests.sh file."""
    template_mappings = {
        'project_name': self._project_definition.name,
    }

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)


class TravisRunChecksScriptWriter(interface.DependencyFileWriter):
  """Travis-CI run_checks.sh file writer."""

  PATH = os.path.join('config', 'travis', 'run_checks.sh')

  _PROJECTS_WITH_TYPING = frozenset(['dfdatetime', 'dfwinreg'])

  def Write(self):
    """Writes a runtests.sh file."""
    paths_to_lint = [self._project_definition.name]
    for path_to_lint in ('config', 'scripts', 'tests', 'tools'):
      if os.path.isdir(path_to_lint):
        paths_to_lint.append(path_to_lint)

    paths_to_lint = sorted(paths_to_lint)

    # Disabled for now since Python 3.8 and pylint fails to lint setup.py
    # if os.path.isfile('setup.py'):
    #   paths_to_lint.insert(0, 'setup.py')

    template_mappings = {
        'paths_to_lint': ' '.join(paths_to_lint),
        'project_name': self._project_definition.name,
    }

    if self._project_definition.name in self._PROJECTS_WITH_TYPING:
      template_file = 'run_checks-pylint_and_mypy.sh'
    else:
      template_file = 'run_checks-pylint.sh'

    template_file = os.path.join(
        self._l2tdevtools_path, 'data', 'templates', 'travis', template_file)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)


class TravisRunPython3ScriptWriter(interface.DependencyFileWriter):
  """Travis-CI run_python3.sh file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'travis', 'run_python3.sh')

  PATH = os.path.join('config', 'travis', 'run_python3.sh')

  def Write(self):
    """Writes a runtests.sh file."""
    template_mappings = {}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)


class TravisRunTestsScriptWriter(interface.DependencyFileWriter):
  """Travis-CI runtests.sh file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'travis', 'runtests.sh')

  PATH = os.path.join('config', 'travis', 'runtests.sh')

  def Write(self):
    """Writes a runtests.sh file."""
    template_mappings = {
        'project_name': self._project_definition.name,
    }

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)


class TravisRunWithTimeoutScriptWriter(interface.DependencyFileWriter):
  """Travis-CI run_with_timeout.sh file writer."""

  _TEMPLATE_FILE = os.path.join(
      'data', 'templates', 'travis', 'run_with_timeout.sh')

  PATH = os.path.join('config', 'travis', 'run_with_timeout.sh')

  def Write(self):
    """Writes a run_with_timeout.sh file."""
    template_mappings = {}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
