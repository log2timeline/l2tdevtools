# -*- coding: utf-8 -*-
"""Writer for .pylintrc files."""

import os

from l2tdevtools.dependency_writers import interface


class PylintRcWriter(interface.DependencyFileWriter):
  """Pylint.rc file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', '.pylintrc')

  PATH = '.pylintrc'

  def Write(self):
    """Writes a .pylintrc file."""
    dependencies = self._dependency_helper.GetPylintRcExtensionPkgs()

    template_mappings = {'extension_pkg_allow_list': ','.join(dependencies)}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    with open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
