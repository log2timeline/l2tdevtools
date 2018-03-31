# -*- coding: utf-8 -*-
"""Writer for dependencies.py files."""

from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class DependenciesPyWriter(interface.DependencyFileWriter):
  """Dependencies.py file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'dependencies.py')

  PATH = os.path.join('plaso', 'dependencies.py')

  def Write(self):
    """Writes a dependencies.py file."""
    dependencies = sorted(
        self._dependency_helper.dependencies.values(),
        key=lambda dependency: dependency.name.lower())

    python_dependencies = []
    for dependency in dependencies:
      if dependency.maximum_version:
        maximum_version = '\'{0:s}\''.format(dependency.maximum_version)
      else:
        maximum_version = 'None'

      python_dependency = (
          '    \'{0:s}\': (\'{1:s}\', \'{2:s}\', {3:s}, {4!s})').format(
              dependency.name, dependency.version_property or '',
              dependency.minimum_version or '', maximum_version,
              not dependency.is_optional)

      python_dependencies.append(python_dependency)

    python_dependencies = ',\n'.join(python_dependencies)

    template_mappings = {'python_dependencies': python_dependencies}

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
