# -*- coding: utf-8 -*-
"""Writer for requirements.txt files."""

from __future__ import unicode_literals

from l2tdevtools.dependency_writers import interface


class RequirementsWriter(interface.DependencyFileWriter):
  """Requirements.txt file writer."""

  PATH = 'requirements.txt'

  _FILE_HEADER = ['pip >= 7.0.0']

  def Write(self):
    """Writes a requirements.txt file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    dependencies = self._dependency_helper.GetInstallRequires()
    for dependency in dependencies:
      file_content.append('{0:s}'.format(dependency))

    file_content.append('')

    file_content = '\n'.join(file_content)
    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
