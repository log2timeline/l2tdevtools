# -*- coding: utf-8 -*-
"""Writer for .pylintrc files."""

from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class PylintRcWriter(interface.DependencyFileWriter):
  """Pylint.rc file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', '.pylintrc')

  PATH = '.pylintrc'

  def Write(self):
    """Writes a .travis.yml file."""
    dependencies = self._dependency_helper.GetPylintRcExtensionPkgs()

    template_mappings = {'extension_pkg_whitelist': ','.join(dependencies)}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
