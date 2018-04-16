# -*- coding: utf-8 -*-
"""Writer for setup configuration and script files."""

from __future__ import unicode_literals

import os
import textwrap

from l2tdevtools.dependency_writers import interface


class SetupCfgWriter(interface.DependencyFileWriter):
  """Setup configuration file writer."""

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


class SetupPyWriter(interface.DependencyFileWriter):
  """Setup script file writer."""

  _TEMPLATE_FILE = os.path.join('data', 'templates', 'setup.py')

  PATH = os.path.join('setup.py')

  def Write(self):
    """Writes a setup.py file."""
    # Width is 80 characters minus 4 spaces, 2 single quotes and 1 comma.
    text_wrapper = textwrap.TextWrapper(drop_whitespace=False, width=73)

    description_short = text_wrapper.wrap(
        self._project_definition.description_short)
    description_short = '\n'.join([
        '    \'{0:s}\''.format(line) for line in description_short])

    description_long = text_wrapper.wrap(
        self._project_definition.description_long)
    description_long = '\n'.join([
        '    \'{0:s}\''.format(line) for line in description_long])

    template_mappings = {
        'description_long': description_long,
        'description_short': description_short,
        'project_name_description': self._project_definition.name_description,
        'project_name': self._project_definition.name,
    }

    template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
    file_content = self._GenerateFromTemplate(template_file, template_mappings)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
