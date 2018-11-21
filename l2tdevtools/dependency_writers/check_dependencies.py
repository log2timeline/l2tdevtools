# -*- coding: utf-8 -*-
"""Writer for check_dependencies script."""

from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class CheckDependenciesWriter(interface.DependencyFileWriter):
  """Check dependencies script writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'check_dependencies.py')

  PATH = os.path.join('utils', 'check_dependencies.py')

  def Write(self):
    """Writes a check_dependencies.py file."""
    template_mappings = {}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
