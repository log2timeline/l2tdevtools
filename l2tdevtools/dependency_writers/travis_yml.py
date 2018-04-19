# -*- coding: utf-8 -*-
"""Writer for travis.yml files."""

from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class TravisYMLWriter(interface.DependencyFileWriter):
  """Travis.yml file writer."""

  _TEMPLATE_DIRECTORY = os.path.join('data', 'templates', '.travis.yml')

  PATH = '.travis.yml'

  def Write(self):
    """Writes a .travis.yml file."""
    template_mappings = {}

    file_content = []

    template_file = os.path.join(
        self._l2tdevtools_path, self._TEMPLATE_DIRECTORY, 'header')
    template_data = self._GenerateFromTemplate(template_file, template_mappings)
    file_content.append(template_data)

    if self._project_definition.name in ('dfvfs', 'plaso'):
      template_file = os.path.join(
          self._l2tdevtools_path, self._TEMPLATE_DIRECTORY, 'jenkins')
      template_data = self._GenerateFromTemplate(template_file, template_mappings)
      file_content.append(template_data)

    template_file = os.path.join(
        self._l2tdevtools_path, self._TEMPLATE_DIRECTORY, 'footer')
    template_data = self._GenerateFromTemplate(template_file, template_mappings)
    file_content.append(template_data)

    file_content = ''.join(file_content)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
