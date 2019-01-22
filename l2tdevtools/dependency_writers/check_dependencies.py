# -*- coding: utf-8 -*-
"""Writer for check_dependencies script."""

from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class CheckDependenciesWriter(interface.DependencyFileWriter):
  """Check dependencies script writer."""

  _TEMPLATE_DIRECTORY = os.path.join('data', 'templates')

  PATH = os.path.join('utils', 'check_dependencies.py')

  def Write(self):
    """Writes a check_dependencies.py file."""
    template_mappings = {
        'project_name': self._project_definition.name}

    if self._project_definition.name == 'plaso':
      template_file = 'check_dependencies-with_url.py'
    else:
      template_file = 'check_dependencies.py'

    template_file = os.path.join(
        self._l2tdevtools_path, self._TEMPLATE_DIRECTORY, template_file)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
