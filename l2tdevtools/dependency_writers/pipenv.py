# -*- coding: utf-8 -*-
"""Writer for pipenv files."""

from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class PipenvPipfileWriter(interface.DependencyFileWriter):
  """Pipenv Pipfile file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'Pipfile')

  PATH = os.path.join('Pipfile')

  def Write(self):
    """Writes a Pipfile file."""
    dependencies = self._dependency_helper.GetPipenvPackages()

    template_mappings = {
        'dependencies': '\n'.join(dependencies)
    }

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
