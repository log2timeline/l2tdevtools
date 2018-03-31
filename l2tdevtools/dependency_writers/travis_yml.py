# -*- coding: utf-8 -*-
"""Writer for travis.yml files."""
from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class TravisYMLWriter(interface.DependencyFileWriter):
  """Travis.yml file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', '.travis.yml')

  PATH = '.travis.yml'

  def Write(self):
    """Writes a .travis.yml file."""
    template_mappings = {}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
