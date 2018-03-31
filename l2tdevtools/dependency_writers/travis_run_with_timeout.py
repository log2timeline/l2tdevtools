# -*- coding: utf-8 -*-
"""Writer for run_with_timeout.sh files."""
from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class TravisRunWithTimeoutScriptWriter(interface.DependencyFileWriter):
  """Travis-CI run_with_timeout.sh file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'run_with_timeout.sh')

  PATH = os.path.join('config', 'travis', 'run_with_timeout.sh')

  def Write(self):
    """Writes a _with_timeout.sh file."""
    template_mappings = {}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
