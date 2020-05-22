# -*- coding: utf-8 -*-
"""Writer for Jenkins script files."""

from __future__ import unicode_literals

import io
import os

from l2tdevtools.dependency_writers import interface


class LinuxRunEndToEndTestsScriptWriter(interface.DependencyFileWriter):
  """Linux run end-to-end test script file writer."""

  _TEMPLATE_FILE = os.path.join(
      'data', 'templates', 'jenkins_scripts', 'linux_run_end_to_end_tests.sh')

  PATH = os.path.join(
      'config', 'jenkins', 'linux', 'run_end_to_end_tests.sh')

  def Write(self):
    """Writes a Linux run_end_to_end_tests.sh file."""
    if self._project_definition.name == 'dfvfs':
      scripts_directory_option = '--scripts-directory ./examples'
    elif self._project_definition.name == 'plaso':
      scripts_directory_option = '--tools-directory ./tools'
    else:
      scripts_directory_option = '--scripts-directory ./scripts'

    template_mappings = {
        'project_name': self._project_definition.name,
        'scripts_directory_option': scripts_directory_option}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)


class RunPython3EndToEndTestsScriptWriter(interface.DependencyFileWriter):
  """Run Python 3 end-to-end test script file writer."""

  _TEMPLATE_FILE = os.path.join(
      'data', 'templates', 'jenkins_scripts', 'run_end_to_end_tests_py3.sh')

  PATH = os.path.join(
      'config', 'jenkins', 'linux', 'run_end_to_end_tests_py3.sh')

  def Write(self):
    """Writes a run_end_to_end_tests.sh file."""
    template_mappings = {
        'project_name': self._project_definition.name}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
