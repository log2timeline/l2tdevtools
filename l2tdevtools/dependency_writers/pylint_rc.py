# -*- coding: utf-8 -*-
"""Writer for .pylintrc files."""

from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class PylintRcWriter(interface.DependencyFileWriter):
  """Pylint.rc file writer."""

  PATH = '.pylintrc'

  _PROJECTS_WITH_PYLINT2_SUPPORT = (
      'artifacts', 'dfdatetime', 'dfvfs', 'dfwinreg', 'dtfabric', 'dtformats',
      'plaso')

  def Write(self):
    """Writes a .pylintrc file."""
    dependencies = self._dependency_helper.GetPylintRcExtensionPkgs()

    template_mappings = {'extension_pkg_whitelist': ','.join(dependencies)}

    if self._project_definition.name in self._PROJECTS_WITH_PYLINT2_SUPPORT:
      template_file = '.pylintrc2'
    else:
      template_file = '.pylintrc1'

    template_file = os.path.join(
        self._l2tdevtools_path, 'data', 'templates', template_file)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
