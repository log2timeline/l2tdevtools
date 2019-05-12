# -*- coding: utf-8 -*-
"""Writer for tox.ini files."""

from __future__ import unicode_literals

import io
import os

from l2tdevtools.dependency_writers import interface


class ToxIniWriter(interface.DependencyFileWriter):
  """Tox.ini file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'tox.ini')

  PATH = 'tox.ini'

  def Write(self):
    """Writes a tox.ini file."""
    template_mappings = {'project_name': self._project_definition.name}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
