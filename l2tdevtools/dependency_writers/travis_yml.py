# -*- coding: utf-8 -*-
"""Writer for travis.yml files."""

from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class TravisYMLWriter(interface.DependencyFileWriter):
  """Travis.yml file writer."""

  _TEMPLATE_DIRECTORY = os.path.join('data', 'templates', '.travis.yml')

  PATH = '.travis.yml'

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
    return super(TravisYMLWriter, self)._GenerateFromTemplate(
        template_filename, template_mappings)

  def Write(self):
    """Writes a .travis.yml file."""
    template_mappings = {}

    file_content = []

    template_data = self._GenerateFromTemplate('header', template_mappings)
    file_content.append(template_data)

    if self._project_definition.name in ('dfvfs', 'plaso'):
      template_data = self._GenerateFromTemplate('jenkins', template_mappings)
      file_content.append(template_data)

    if self._project_definition.name in ('l2tpreg', 'plaso'):
      template_data = self._GenerateFromTemplate(
          'allow_failures', template_mappings)
      file_content.append(template_data)

    template_data = self._GenerateFromTemplate('footer', template_mappings)
    file_content.append(template_data)

    file_content = ''.join(file_content)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
