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

  _DOC_FILES = ('ACKNOWLEDGEMENTS', 'AUTHORS', 'LICENSE', 'README')

  def Write(self):
    """Writes a setup.cfg file."""
    file_content = []

    if self._project_definition.name in ('dfvfs', 'l2tpreg', 'plaso'):
      file_content.extend(self._SDIST)

    file_content.extend(self._BDIST_RPM)

    doc_files = [
        doc_file for doc_file in self._DOC_FILES if os.path.isfile(doc_file)]

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

  PATH = os.path.join('setup.py')

  _DOC_FILES = ('ACKNOWLEDGEMENTS', 'AUTHORS', 'LICENSE', 'README')

  _PROJECTS_WITH_PACKAGE_DATA = (
      'dfvfs', 'dfwinreg', 'dtformats', 'plaso', 'winregrc')

  _TEMPLATE_DIRECTORY = os.path.join('data', 'templates', 'setup.py')

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
    return super(SetupPyWriter, self)._GenerateFromTemplate(
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

    doc_files = [
        doc_file for doc_file in self._DOC_FILES if os.path.isfile(doc_file)]

    maintainer = self._project_definition.maintainer
    maintainer, _, maintainer_email = maintainer.rpartition('<')
    maintainer_email, _, _ = maintainer_email.rpartition('>')

    if self._project_definition.status == 'experimental':
      development_status = 'Development Status :: 2 - Pre-Alpha'
    elif self._project_definition.status == 'alpha':
      development_status = 'Development Status :: 3 - Alpha'
    elif self._project_definition.status == 'beta':
      development_status = 'Development Status :: 4 - Beta'
    elif self._project_definition.status == 'stable':
      development_status = 'Development Status :: 5 - Production/Stable'
    else:
      development_status = ''

    packages_exclude = ['tests', 'tests.*', 'utils']

    if os.path.isdir('docs'):
      packages_exclude.append('docs')

    scripts_directory = None
    if os.path.isdir('scripts'):
      scripts_directory = 'scripts'
    elif os.path.isdir('tools'):
      scripts_directory = 'tools'

    if scripts_directory:
      packages_exclude.append(scripts_directory)

    packages_exclude = ', '.join([
        '\'{0:s}\''.format(exclude) for exclude in sorted(packages_exclude)])

    template_mappings = {
        'doc_files': ', '.join([
            '\'{0:s}\''.format(doc_file) for doc_file in doc_files]),
        'description_long': description_long,
        'description_short': description_short,
        'development_status': development_status,
        'homepage_url': self._project_definition.homepage_url,
        'maintainer': maintainer.strip(),
        'maintainer_email': maintainer_email.strip(),
        'packages_exclude': packages_exclude,
        'project_name_description': self._project_definition.name_description,
        'project_name': self._project_definition.name,
        'rpm_doc_files': ' '.join(doc_files),
        'scripts_directory': scripts_directory,
    }

    if self._project_definition.name in self._PROJECTS_WITH_PACKAGE_DATA:
      if self._project_definition.name == 'dfvfs':
        package_data_paths = ['dfvfs.lib']
      elif self._project_definition.name == 'plaso':
        package_data_paths = [
            'plaso.parsers', 'plaso.parsers.olecf_plugins',
            'plaso.parsers.winreg_plugins']
      elif self._project_definition.name == 'winreg-kb':
        package_data_paths = ['winregrc']
      else:
        package_data_paths = [self._project_definition.name]

      template_mappings['package_data_paths'] = ',\n'.join([
          '        \'{0:s}\': [\'*.yaml\']'.format(path)
          for path in package_data_paths])

    file_content = []

    if scripts_directory:
      template_data = self._GenerateFromTemplate(
          'header_scripts', template_mappings)
    else:
      template_data = self._GenerateFromTemplate(
          'header', template_mappings)
    file_content.append(template_data)

    template_data = self._GenerateFromTemplate(
        'header_setuptools', template_mappings)
    file_content.append(template_data)

    if self._project_definition.name in ('dfvfs', 'plaso'):
      template_data = self._GenerateFromTemplate(
          'import_sdist', template_mappings)
      file_content.append(template_data)

    for template_file in ('import_module', 'bdist_msi'):
      template_data = self._GenerateFromTemplate(
          template_file, template_mappings)
      file_content.append(template_data)

    if self._project_definition.name in self._PROJECTS_WITH_PACKAGE_DATA:
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

    if self._project_definition.name in self._PROJECTS_WITH_PACKAGE_DATA:
      template_data = self._GenerateFromTemplate(
          'setup_package_data', template_mappings)
      file_content.append(template_data)

    if scripts_directory:
      template_data = self._GenerateFromTemplate(
          'setup_scripts', template_mappings)
      file_content.append(template_data)

    template_data = self._GenerateFromTemplate(
        'setup_data_files', template_mappings)
    file_content.append(template_data)

    if os.path.isdir('data'):
      template_data = self._GenerateFromTemplate(
          'setup_data_files_data', template_mappings)
      file_content.append(template_data)

    template_data = self._GenerateFromTemplate(
        'setup_footer', template_mappings)
    file_content.append(template_data)

    file_content = ''.join(file_content)

    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
