# -*- coding: utf-8 -*-
"""Writer for setup.cfg files."""

from __future__ import unicode_literals

import os

from l2tdevtools.dependency_writers import interface


class SetupCfgWriter(interface.DependencyFileWriter):
  """Setup.cfg file writer."""

  PATH = 'setup.cfg'

  _SDIST = [
      '[sdist]', 'template = MANIFEST.in', 'manifest = MANIFEST', '',
      '[sdist_test_data]', 'template = MANIFEST.test_data.in',
      'manifest = MANIFEST.test_data', ''
  ]  # yapf: disable

  _BDIST_RPM = ['[bdist_rpm]', 'release = 1', 'packager = {maintainer:s}']

  def Write(self):
    """Writes a setup.cfg file."""
    file_content = []

    if self._project_definition.name in ('dfvfs', 'l2tpreg', 'plaso'):
      file_content.extend(self._SDIST)

    file_content.extend(self._BDIST_RPM)

    doc_files = ['AUTHORS', 'LICENSE', 'README']

    if os.path.isfile('ACKNOWLEDGEMENTS'):
      doc_files.append('ACKNOWLEDGEMENTS')

    for index, doc_file in enumerate(sorted(doc_files)):
      if index == 0:
        file_content.append('doc_files = {0:s}'.format(doc_file))
      else:
        file_content.append('            {0:s}'.format(doc_file))

    file_content.append('build_requires = python-setuptools')

    python2_dependencies = self._dependency_helper.GetRPMRequires(
        python_version=2)

    for index, dependency in enumerate(python2_dependencies):
      if index == 0:
        file_content.append('requires = {0:s}'.format(dependency))
      else:
        file_content.append('           {0:s}'.format(dependency))

    file_content.append('')

    template_mappings = {'maintainer': self._project_definition.maintainer}

    file_content = '\n'.join(file_content)
    file_content = file_content.format(**template_mappings)
    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
