# -*- coding: utf-8 -*-
"""Writer for appveyor.yml files."""

import io
import os

from l2tdevtools.dependency_writers import interface


class AppveyorYmlWriter(interface.DependencyFileWriter):
  """Appveyor.yml file writer."""

  _TEMPLATE_DIRECTORY = os.path.join('data', 'templates', 'appveyor.yml')

  PATH = os.path.join('appveyor.yml')

  _PROJECTS_WITHOUT_BUILD = frozenset([
      'dtformats', 'esedbrc', 'olecfrc', 'vstools', 'winevtrc', 'winregrc'])

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
    template_mappings = {
        'pypi_token': self._project_definition.pypi_token or ''}

    file_content = []

    template_data = self._GenerateFromTemplate('environment', template_mappings)
    file_content.append(template_data)

    if self._project_definition.name not in self._PROJECTS_WITHOUT_BUILD:
      template_data = self._GenerateFromTemplate(
          'pypi_token', template_mappings)
      file_content.append(template_data)

    template_data = self._GenerateFromTemplate('matrix', template_mappings)
    file_content.append(template_data)

    template_data = self._GenerateFromTemplate('install', template_mappings)
    file_content.append(template_data)

    if self._project_definition.name != 'l2tdevtools':
      template_data = self._GenerateFromTemplate(
          'install_l2tdevtools', template_mappings)
      file_content.append(template_data)

    if self._project_definition.name in self._PROJECTS_WITHOUT_BUILD:
      template_filename = 'build_off'
    else:
      template_filename = 'build'

    template_data = self._GenerateFromTemplate(
       template_filename, template_mappings)
    file_content.append(template_data)

    template_data = self._GenerateFromTemplate('test_script', template_mappings)
    file_content.append(template_data)

    if self._project_definition.name not in self._PROJECTS_WITHOUT_BUILD:
      template_data = self._GenerateFromTemplate('artifacts', template_mappings)
      file_content.append(template_data)

      template_data = self._GenerateFromTemplate(
          'deploy_script', template_mappings)
      file_content.append(template_data)

    file_content = ''.join(file_content)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
