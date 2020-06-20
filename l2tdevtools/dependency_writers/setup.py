# -*- coding: utf-8 -*-
"""Writer for setup configuration and script files."""

from __future__ import unicode_literals

import glob
import io
import os
import textwrap

from l2tdevtools.dependency_writers import interface


class SetupCfgWriter(interface.DependencyFileWriter):
  """Setup configuration file writer."""

  PATH = 'setup.cfg'

  _DOC_FILES = ('ACKNOWLEDGEMENTS', 'AUTHORS', 'LICENSE', 'README')

  _PROJECTS_WITH_SDIST_TEST_DATA = (
      'dfvfs', 'dfwinreg', 'plaso')

  _TEMPLATE_DIRECTORY = os.path.join('data', 'templates', 'setup.cfg')

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
    return super(SetupCfgWriter, self)._GenerateFromTemplate(
        template_filename, template_mappings)

  def Write(self):
    """Writes a setup.cfg file."""
    doc_files = [
        doc_file for doc_file in self._DOC_FILES if os.path.isfile(doc_file)]

    formatted_doc_files = []
    for index, doc_file in enumerate(sorted(doc_files)):
      if index == 0:
        line = 'doc_files = {0:s}'.format(doc_file)
      else:
        line = '            {0:s}'.format(doc_file)
      formatted_doc_files.append(line)

    python3_dependencies = self._dependency_helper.GetRPMRequires(
        python_version=3)

    formatted_requires = []
    for index, dependency in enumerate(python3_dependencies):
      if index == 0:
        line = 'requires = {0:s}'.format(dependency)
      else:
        line = '           {0:s}'.format(dependency)
      formatted_requires.append(line)

    formatted_requires.append('')

    template_mappings = {
        'doc_files': '\n'.join(formatted_doc_files),
        'maintainer': self._project_definition.maintainer,
        'requires': '\n'.join(formatted_requires)}

    file_content = []

    template_data = self._GenerateFromTemplate('metadata', template_mappings)
    file_content.append(template_data)

    if self._project_definition.name in self._PROJECTS_WITH_SDIST_TEST_DATA:
      template_data = self._GenerateFromTemplate(
          'sdist_test_data', template_mappings)
      file_content.append(template_data)

    template_data = self._GenerateFromTemplate('bdist_rpm', template_mappings)
    file_content.append(template_data)

    template_data = self._GenerateFromTemplate('bdist_wheel', template_mappings)
    file_content.append(template_data)

    file_content = ''.join(file_content)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)


class SetupPyWriter(interface.DependencyFileWriter):
  """Setup script file writer."""

  PATH = os.path.join('setup.py')

  _DOC_FILES = ('ACKNOWLEDGEMENTS', 'AUTHORS', 'LICENSE', 'README')

  _PROJECTS_WITH_PACKAGE_DATA = (
      'dfvfs', 'dfwinreg', 'dtformats', 'plaso', 'winregrc')

  _PROJECTS_WITH_PYTHON3_AS_DEFAULT = ('plaso', )

  _PROJECTS_WITH_SDIST_TEST_DATA = (
      'dfvfs', 'dfwinreg', 'plaso')

  _TEMPLATE_DIRECTORY = os.path.join('data', 'templates', 'setup.py')

  def _DetermineSubmoduleLevels(self, project_name):
    """Determines the number of submodule levels.

    Args:
      project_name (str): name of the project.

    Return:
      int: number of submodule levels.
    """
    submodule_glob = project_name
    submodule_levels = 0

    while submodule_levels < 10:
      submodule_glob = '{0:s}/*'.format(submodule_glob)
      submodule_paths = [
          path for path in glob.glob(submodule_glob)
          if os.path.isdir(path) and os.path.basename(path) != '__pycache__']

      if not submodule_paths:
        break

      submodule_levels += 1

    return submodule_levels

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

    if self._project_definition.name in self._PROJECTS_WITH_PYTHON3_AS_DEFAULT:
      shebang = '#!/usr/bin/env python3'
    else:
      shebang = '#!/usr/bin/env python'

    if self._project_definition.name in ('artifacts', 'plaso'):
      data_files_path = 'share/{0:s}'.format(self._project_definition.name)
    else:
      data_files_path = 'share/{0:s}/data'.format(self._project_definition.name)

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

    data_directory = None
    if os.path.isdir('data'):
      data_directory = 'data'

    scripts_directory = None
    if os.path.isdir('scripts'):
      scripts_directory = 'scripts'
    elif os.path.isdir('tools'):
      scripts_directory = 'tools'

    if scripts_directory:
      packages_exclude.append(scripts_directory)

    packages_exclude = ', '.join([
        '\'{0:s}\''.format(exclude) for exclude in sorted(packages_exclude)])

    submodule_levels = self._DetermineSubmoduleLevels(
        self._project_definition.name)

    python3_package_module_prefix = '%{{{{python3_sitelib}}}}/{0:s}'.format(
        self._project_definition.name)
    python3_package_files = [
        '{0:s}/*.py'.format(python3_package_module_prefix)]

    yaml_glob = os.path.join(python3_package_module_prefix[21:], '*.yaml')
    if glob.glob(yaml_glob):
      python3_package_files.append(
          '{0:s}/*.yaml'.format(python3_package_module_prefix))

    for _ in range(submodule_levels):
      python3_package_module_prefix = '{0:s}/*'.format(
          python3_package_module_prefix)
      python3_package_files.append(
          '{0:s}/*.py'.format(python3_package_module_prefix))

      yaml_glob = os.path.join(python3_package_module_prefix[21:], '*.yaml')
      if glob.glob(yaml_glob):
        python3_package_files.append(
            '{0:s}/*.yaml'.format(python3_package_module_prefix))

    python3_package_files.extend([
        '%{{python3_sitelib}}/{0:s}*.egg-info/*',
        '',
        '%exclude %{{_prefix}}/share/doc/*'])

    python3_package_module_prefix = '%{{{{python3_sitelib}}}}/{0:s}'.format(
        self._project_definition.name)
    python3_package_files.append(
        '%exclude {0:s}/__pycache__/*'.format(python3_package_module_prefix))

    for _ in range(submodule_levels):
      python3_package_module_prefix = '{0:s}/*'.format(
          python3_package_module_prefix)
      python3_package_files.append(
          '%exclude {0:s}/__pycache__/*'.format(python3_package_module_prefix))

    if not data_directory and scripts_directory:
      python3_package_files.append('%exclude %{{_bindir}}/*.py')

    python3_package_files = ',\n'.join([
        '              \'{0:s}\''.format(package_file)
        for package_file in python3_package_files])
    python3_package_files = python3_package_files.format(
        self._project_definition.name)

    rpm_doc_files = [
        doc_file for doc_file in doc_files if doc_file != 'LICENSE']
    rpm_license_file = 'LICENSE'

    template_mappings = {
        'data_files_path': data_files_path,
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
        'python3_package_files': python3_package_files,
        'rpm_doc_files': ' '.join(rpm_doc_files),
        'rpm_license_file': rpm_license_file,
        'shebang': shebang,
        'scripts_directory': scripts_directory,
    }

    if self._project_definition.name in self._PROJECTS_WITH_PACKAGE_DATA:
      if self._project_definition.name == 'dfvfs':
        package_data_paths = ['dfvfs.lib']
      elif self._project_definition.name == 'plaso':
        package_data_paths = [
            'plaso.parsers', 'plaso.parsers.esedb_plugins',
            'plaso.parsers.olecf_plugins', 'plaso.parsers.plist_plugins',
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

    if self._project_definition.name in self._PROJECTS_WITH_SDIST_TEST_DATA:
      template_data = self._GenerateFromTemplate(
          'import_sdist', template_mappings)
      file_content.append(template_data)

    for template_file in ('import_module', 'bdist_msi', 'bdist_rpm-start'):
      template_data = self._GenerateFromTemplate(
          template_file, template_mappings)
      file_content.append(template_data)

    if data_directory and scripts_directory:
      template_file = 'bdist_rpm-with_data_and_tools'
    elif data_directory:
      template_file = 'bdist_rpm-with_data'
    else:
      template_file = 'bdist_rpm'

    template_data = self._GenerateFromTemplate(template_file, template_mappings)
    file_content.append(template_data)

    template_data = self._GenerateFromTemplate(
        'setup_header', template_mappings)
    file_content.append(template_data)

    if self._project_definition.name in self._PROJECTS_WITH_SDIST_TEST_DATA:
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

    if data_directory:
      if self._project_definition.name == 'plaso':
        template_file = 'setup_data_files-with_data-plaso'
      else:
        template_file = 'setup_data_files-with_data'

      template_data = self._GenerateFromTemplate(
          template_file, template_mappings)
      file_content.append(template_data)

    template_data = self._GenerateFromTemplate(
        'setup_footer', template_mappings)
    file_content.append(template_data)

    file_content = ''.join(file_content)

    with io.open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
