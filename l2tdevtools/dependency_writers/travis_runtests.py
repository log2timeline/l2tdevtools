# -*- coding: utf-8 -*-
"""Writer for runtests.sh files."""
from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class TravisRunTestsScriptWriter(interface.DependencyFileWriter):
  """Travis-CI runtests.sh file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'runtests.sh')

  PATH = os.path.join('config', 'travis', 'runtests.sh')

  def Write(self):
    """Writes a runtests.sh file."""
    paths_to_lint = [self._project_definition.name]
    for path_to_lint in ('config', 'scripts', 'tests', 'tools'):
      if os.path.isdir(path_to_lint):
        paths_to_lint.append(path_to_lint)

    paths_to_lint = sorted(paths_to_lint)
    if os.path.isfile('setup.py'):
      paths_to_lint.insert(0, 'setup.py')

    template_mappings = {
        'project_name': self._project_definition.name,
        'paths_to_lint': ' '.join(paths_to_lint)
    }

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
