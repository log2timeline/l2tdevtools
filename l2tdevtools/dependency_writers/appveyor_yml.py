# -*- coding: utf-8 -*-
"""Writer for appveyor.yml files."""

from __future__ import unicode_literals

import io
import os

from l2tdevtools.dependency_writers import interface


class AppveyorYmlWriter(interface.DependencyFileWriter):
  """Appveyor.yml file writer."""

  _TEMPLATE_DIRECTORY = os.path.join('data', 'templates', 'appveyor.yml')

  PATH = os.path.join('appveyor.yml')

  def _GenerateFromTemplate(self, template_filename, template_mappings):
    """Generates file context based on a template file.

    Args:
      template_filename (str): path of the template file.
      template_mappings (dict[str, str]): template mappings, where the key
          maps to the name of a template variable.

    Returns:
      str: output based on the template string.

    Raises:
      RuntimeError: if the template cannot be formatted.
    """
    template_filename = os.path.join(
        self._l2tdevtools_path, self._TEMPLATE_DIRECTORY, template_filename)
    return super(AppveyorYmlWriter, self)._GenerateFromTemplate(
        template_filename, template_mappings)

  def Write(self):
    """Writes an appveyor.yml file."""
    python3_dependencies = self._dependency_helper.GetL2TBinaries(
        python_version=3)

    python3_dependencies.extend(self._test_dependency_helper.GetL2TBinaries(
        python_version=3))

    template_mappings = {
        'python3_dependencies': ' '.join(sorted(set(python3_dependencies)))
    }

    file_content = []

    template_data = self._GenerateFromTemplate('environment', template_mappings)
    file_content.append(template_data)

    template_data = self._GenerateFromTemplate('install', template_mappings)
    file_content.append(template_data)

    template_data = self._GenerateFromTemplate(
        'install_l2tdevtools', template_mappings)
    file_content.append(template_data)

    template_data = self._GenerateFromTemplate(
        'install_windows_python3', template_mappings)
    file_content.append(template_data)

    template_data = self._GenerateFromTemplate('build', template_mappings)
    file_content.append(template_data)

    template_data = self._GenerateFromTemplate('test_script', template_mappings)
    file_content.append(template_data)

    file_content = ''.join(file_content)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
