# -*- coding: utf-8 -*-
"""Writer for MacOS script files."""

from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class MacOSInstallScriptWriter(interface.DependencyFileWriter):
  """MacOS installation script file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'macos_install.sh')

  PATH = os.path.join('config', 'macos', 'install.sh')

  def Write(self):
    """Writes an install.sh file."""
    dependencies = self._dependency_helper.GetL2TBinaries(
        platform='macos', python_version=2)

    template_mappings = {
        'dependencies': ' '.join(dependencies),
        'project_name': self._project_definition.name,
    }

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class MacOSMakeDistScriptWriter(interface.DependencyFileWriter):
  """MacOS make distribution script file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'macos_make_dist.sh')

  PATH = os.path.join('config', 'macos', 'make_dist.sh')

  def Write(self):
    """Writes a make_dist.sh file."""
    dependencies = self._dependency_helper.GetL2TBinaries(
        platform='macos', python_version=2)

    template_mappings = {
        'dependencies': ' '.join(dependencies),
        'project_name': self._project_definition.name,
    }

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class MacOSUninstallScriptWriter(interface.DependencyFileWriter):
  """MacOS uninstallation script file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'macos_uninstall.sh')

  PATH = os.path.join('config', 'macos', 'uninstall.sh')

  def Write(self):
    """Writes an uninstall.sh file."""
    dependencies = self._dependency_helper.GetL2TBinaries(
        platform='macos', python_version=2)

    template_mappings = {
        'dependencies': ' '.join(dependencies),
        'project_name': self._project_definition.name,
    }

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
