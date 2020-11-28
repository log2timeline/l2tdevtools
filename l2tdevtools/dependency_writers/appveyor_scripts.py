# -*- coding: utf-8 -*-
"""Writer for AppVeyor script files."""

from __future__ import unicode_literals

import io
import os

from l2tdevtools.dependency_writers import interface


class AppVeyorInstallPS1ScriptWriter(interface.DependencyFileWriter):
  """AppVeyor install.ps1 script file writer."""

  _TEMPLATE_FILE = os.path.join(
      'data', 'templates', 'appveyor_scripts', 'install.ps1')

  PATH = os.path.join('config', 'appveyor', 'install.ps1')

  def Write(self):
    """Writes an install.ps1 file."""
    dependencies = self._dependency_helper.GetL2TBinaries(python_version=3)
    dependencies.extend(self._test_dependency_helper.GetL2TBinaries(
        python_version=3))

    template_mappings = {
        'dependencies': ' '.join(sorted(set(dependencies)))
    }
    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)


class AppVeyorInstallSHScriptWriter(interface.DependencyFileWriter):
  """AppVeyor install.sh script file writer."""

  _TEMPLATE_FILE = os.path.join(
      'data', 'templates', 'appveyor_scripts', 'install.sh')

  PATH = os.path.join('config', 'appveyor', 'install.sh')

  def Write(self):
    """Writes an install.sh file."""
    template_mappings = {}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)


class AppVeyorRuntestsSHScriptWriter(interface.DependencyFileWriter):
  """AppVeyor runtests.sh script file writer."""

  _TEMPLATE_FILE = os.path.join(
      'data', 'templates', 'appveyor_scripts', 'runtests.sh')

  PATH = os.path.join('config', 'appveyor', 'runtests.sh')

  def Write(self):
    """Writes an runtests.sh file."""
    template_mappings = {}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
