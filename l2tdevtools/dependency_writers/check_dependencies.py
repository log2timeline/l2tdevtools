# -*- coding: utf-8 -*-
"""Writer for check_dependencies script."""

import io
import os

from l2tdevtools.dependency_writers import interface


class CheckDependenciesWriter(interface.DependencyFileWriter):
  """Check dependencies script writer."""

  _TEMPLATE_DIRECTORY = os.path.join('data', 'templates')

  _PROJECTS_WITH_PYTHON3_AS_DEFAULT = ('l2tscaffolder', 'plaso')

  PATH = os.path.join('utils', 'check_dependencies.py')

  def Write(self):
    """Writes a check_dependencies.py file."""
    if self._project_definition.name in self._PROJECTS_WITH_PYTHON3_AS_DEFAULT:
      shebang = '#!/usr/bin/env python3'
    else:
      shebang = '#!/usr/bin/env python'

    template_mappings = {
        'project_name': self._project_definition.name,
        'shebang': shebang,
    }

    if self._project_definition.name == 'plaso':
      template_file = 'check_dependencies-with_url.py'
    else:
      template_file = 'check_dependencies.py'

    template_file = os.path.join(
        self._l2tdevtools_path, self._TEMPLATE_DIRECTORY, template_file)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
