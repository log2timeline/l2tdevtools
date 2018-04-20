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

  _TEMPLATE_DIRECTORY = os.path.join('data', 'templates', 'setup.py')

  PATH = os.path.join('setup.py')

  def _GenerateFromTemplate(self, template_filename, template_mappings):
    """Generates file context based on a template file.

    Args:
      template_filename (str): path of the template file.
      template_mappings (dict[str, str]): template mappings, where the key
          maps to the name of a template variable.

    Returns:
      str: output based on the template string.

    Raises:
      RuntimeError: if the template cannot be formatted.
    """
    template_filename = os.path.join(
        self._l2tdevtools_path, self._TEMPLATE_DIRECTORY, template_filename)
    super(SetupPyWriter, self)._GenerateFromTemplate(
        template_filename, template_mappings)

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

    file_content = []

    template_data = self._GenerateFromTemplate('header', template_mappings)
    file_content.append(template_data)

    if self._project_definition.name in ('dfvfs', 'plaso'):
      template_data = self._GenerateFromTemplate(
          'import_sdist', template_mappings)
      file_content.append(template_data)

    for template_file in ('import_module', 'bdist_msi'):
      template_data = self._GenerateFromTemplate(
          template_file, template_mappings)
      file_content.append(template_data)

    if self._project_definition.name in ('dfvfs', 'dfwinreg'):
      template_file = 'bdist_rpm_package_data'
    else:
      template_file = 'bdist_rpm'

    template_data = self._GenerateFromTemplate(template_file, template_mappings)
    file_content.append(template_data)

    template_data = self._GenerateFromTemplate(
        'setup_header', template_mappings)
    file_content.append(template_data)

    if self._project_definition.name in ('dfvfs', 'plaso'):
      template_file = 'setup_cmdclass_sdist'
    else:
      template_file = 'setup_cmdclass'

    template_data = self._GenerateFromTemplate(template_file, template_mappings)
    file_content.append(template_data)

    template_data = self._GenerateFromTemplate(
        'setup_classifiers', template_mappings)
    file_content.append(template_data)

    if self._project_definition.name in ('dfvfs', 'dfwinreg'):
      template_data = self._GenerateFromTemplate(
          'setup_package_data', template_mappings)
      file_content.append(template_data)

    template_data = self._GenerateFromTemplate(
        'setup_footer', template_mappings)
    file_content.append(template_data)

    file_content = ''.join(file_content)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
