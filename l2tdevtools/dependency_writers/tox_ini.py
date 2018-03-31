# -*- coding: utf-8 -*-
"""Writer for tox.ini files."""

from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class ToxIniWriter(interface.DependencyFileWriter):
  """Tox.ini file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'tox.ini')

  PATH = 'tox.ini'

  def Write(self):
    """Writes a tox.ini file."""
    test_dependencies = ['mock', 'pytest']
    if self._project_definition.name == 'artifacts':
      test_dependencies.append('yapf')

    test_dependencies = '\n'.join(
        ['    {0:s}'.format(dependency) for dependency in test_dependencies])

    template_mappings = {
        'project_name': self._project_definition.name,
        'test_dependencies': test_dependencies
    }

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
