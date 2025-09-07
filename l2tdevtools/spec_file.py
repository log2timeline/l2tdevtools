# -*- coding: utf-8 -*-
"""RPM spec file generator."""

import datetime
import glob
import os

from setuptools.config import setupcfg

from l2tdevtools import dependencies


class RPMSpecFileGenerator(object):
  """Class that helps in generating RPM spec files."""

  _EMAIL_ADDRESS = (
      'log2timeline development team <log2timeline-dev@googlegroups.com>')

  _DOC_FILENAMES = [
      'CHANGES', 'CHANGES.txt', 'CHANGES.TXT',
      'README', 'README.txt', 'README.TXT']

  _LICENSE_FILENAMES = [
      'LICENSE', 'LICENSE.txt', 'LICENSE.TXT']

  _SPEC_TEMPLATE_DATA_PACKAGE_DEFINITION = [
      '%package -n %{{name}}-data',
      'Summary: Data files for {summary:s}',
      '',
      '%description -n %{{name}}-data',
      '{description:s}',
      '',
      '']

  _SPEC_TEMPLATE_PYTHON3_BODY = [
      '# %generate_buildrequires',
      '# %pyproject_buildrequires -R',
      '#',
      '%prep',
      '%autosetup -p1 -n %{{name}}-%{{version}}',
      '',
      '%build',
      '%pyproject_wheel',
      '',
      '%install',
      '%pyproject_install',
      '',
      '']

  _SPEC_TEMPLATE_TOOLS_PACKAGE_DEFINITION = [
      '%package -n %{{name}}-tools',
      'Requires: python3-{project_name:s} >= %{{version}}',
      'Summary: Tools for {summary:s}',
      '',
      '%description -n %{{name}}-tools',
      '{description:s}',
      '',
      '']

  LOG_FILENAME = 'build.log'

  def __init__(self, data_path):
    """Initializes the RPM spec file generator.

    Args:
      data_path (str): path to the data directory which contains the RPM
          templates sub directory.
    """
    super(RPMSpecFileGenerator, self).__init__()
    self._data_path = data_path

  def _GenerateSpecFile(
      self, project_definition, source_directory, source_package_filename,
      project_name, rpm_build_dependencies, output_file_object):
    """Generates a RPM spec file.

    Args:
      project_definition (ProjectDefinition): project definition.
      source_directory (str): path of the source directory.
      source_package_filename (str): name of the source package.
      project_name (str): name of the project.
      rpm_build_dependencies (list[str]): RPM build dependencies.
      output_file_object (file): output file-like object to write to.

    Returns:
      bool: True if successful, False otherwise.

    Raises:
      ValueError: if required configuration values are missing.
    """
    configuration = {
        'description': None,
        'name': None,
        'license': None,
        'summary': None,
        'url': None,
        'vendor': None,
        'version': None}

    has_data_package = False

    python_module_name = project_name

    if os.path.isdir(os.path.join(source_directory, 'scripts')):
      has_tools_package = True
    elif os.path.isdir(os.path.join(source_directory, 'tools')):
      has_tools_package = True
    elif os.path.isdir(os.path.join(
        source_directory, python_module_name, 'scripts')):
      has_tools_package = True
    else:
      has_tools_package = False

    if project_definition.srpm_name:
      package_name = project_definition.srpm_name
    elif project_definition.rpm_name:
      package_name = project_definition.rpm_name
    else:
      package_name = project_name

    if package_name.startswith('python-'):
      package_name = package_name[7:]

    if project_definition.description_long:
      configuration['description'] = (
          f'{project_definition.description_long:s}\n\n')

    if project_definition.description_short:
      configuration['summary'] = project_definition.description_short

    if project_definition.homepage_url:
      configuration['url'] = project_definition.homepage_url

    if project_definition.license:
      configuration['license'] = project_definition.license

    if project_definition.maintainer:
      configuration['vendor'] = project_definition.maintainer

    # TODO: add support for pyproject.toml
    # build.util.project_wheel_metadata

    setup_cfg_file = os.path.join(source_directory, 'setup.cfg')
    if os.path.isfile(setup_cfg_file):
      setup_cfg = setupcfg.read_configuration(setup_cfg_file)
      setup_cfg_metadata = setup_cfg.get('metadata', {})

      if not configuration['version']:
        configuration['version'] = setup_cfg_metadata.get('version', None)

      if not configuration['license']:
        configuration['license'] = setup_cfg_metadata.get('license', None)

      if not configuration['description']:
        configuration['description'] = setup_cfg_metadata.get(
            'long_description', None)

      if not configuration['summary']:
        configuration['summary'] = setup_cfg_metadata.get('description', None)

      if not configuration['url']:
        configuration['url'] = setup_cfg_metadata.get('url', None)

      if not configuration['vendor']:
        configuration['vendor'] = setup_cfg_metadata.get('maintainer', None)

    if not configuration['version']:
      for version_file in glob.glob(os.path.join(
          source_directory, '**', 'version.py')):
        with open(version_file, 'r', encoding='utf8') as file_object:
          for line in file_object:
            if '__version__' in line and '=' in line:
              version = line.strip().rsplit('=', maxsplit=1)[-1]
              configuration['version'] = version.strip().strip('\'').strip('"')

    if not configuration['version']:
      for version_file in glob.glob(os.path.join(
          source_directory, '**', '__init__.py')):
        with open(version_file, 'r', encoding='utf8') as file_object:
          for line in file_object:
            if '__version__' in line and '=' in line:
              version = line.strip().rsplit('=', maxsplit=1)[-1]
              configuration['version'] = version.strip().strip('\'').strip('"')

    if rpm_build_dependencies:
      build_requires = rpm_build_dependencies
    else:
      build_requires = self._SplitRequires(build_requires)

    configuration['name'] = project_name

    for key, value in configuration.items():
      if value is None:
        raise ValueError(f'Missing configuration value: {key:s}')

    self._WriteSourcePackageDefinition(
        output_file_object, source_package_filename, project_definition,
        build_requires, configuration)

    if project_name != package_name:
      python_package_name = f'python3-{package_name:s}'
    else:
      python_package_name = 'python3-%{name}'

    if has_data_package:
      self._WriteDataPackageDefinition(output_file_object, configuration)

    self._WritePython3PackageDefinition(
        project_definition, source_directory, python_package_name,
        configuration, output_file_object)

    if has_tools_package:
      self._WriteToolsPackageDefinition(output_file_object, configuration)

    license_line = self._GetLicenseFileDefinition(source_directory)

    doc_line = self._GetDocumentationFilesDefinition(source_directory)

    self._WritePython3Body(output_file_object, project_name)

    if has_data_package:
      self._WriteDataPackageFiles(output_file_object)

    self._WritePython3PackageFiles(
        output_file_object, project_definition, project_name,
        python_package_name, license_line, doc_line)

    if has_tools_package:
      self._WriteToolsPackageFiles(output_file_object)

    # TODO make this more generic.
    if project_name in ('chardet', 'dtfabric', 'pbr'):
      output_file_object.write((
          '%exclude %{_bindir}/*\n'
          '\n'))

    self._WriteChangeLog(output_file_object, configuration['version'])

    return True

  def _GetDocumentationFilesDefinition(self, source_directory):
    """Retrieves the documentation files definition.

    Args:
      source_directory (str): path of the source directory.

    Returns:
      str: documentation files definition.
    """
    doc_files = []
    for doc_file in self._DOC_FILENAMES:
      doc_file_path = os.path.join(source_directory, doc_file)
      if os.path.exists(doc_file_path):
        doc_files.append(doc_file)

    if not doc_files:
      doc_file_definition = ''
    else:
      doc_files = ' '.join(doc_files)
      doc_file_definition = f'%doc {doc_files:s}\n'

    return doc_file_definition

  def _GetInstallDefinition(self, project_name):
    """Retrieves the install definition.

    Args:
      project_name (str): name of the project.

    Returns:
      str: install definition.
    """
    lines = [
        '%py3_install',
        ('rm -rf %{buildroot}/usr/lib/python*/site-packages/*.dist-info/'
         'requires.txt'),
        'rm -rf %{buildroot}/usr/share/doc/%{name}/']

    if project_name == 'astroid':
      lines.extend([
          'rm -rf %{buildroot}%{python3_sitelib}/astroid/tests'])

    elif project_name == 'pylint':
      lines.extend([
          'rm -rf %{buildroot}%{python3_sitelib}/pylint/test'])

    lines.append('')
    return '\n'.join(lines)

  def _GetLicenseFileDefinition(self, source_directory):
    """Retrieves the license file definition.

    Args:
      source_directory (str): path of the source directory.

    Returns:
      str: license file definition.
    """
    license_file_definition = ''
    for license_file in self._LICENSE_FILENAMES:
      license_file_path = os.path.join(source_directory, license_file)
      if os.path.exists(license_file_path):
        license_file_definition = '%license {0:s}\n'.format(license_file)
        break

    return license_file_definition

  def _SplitRequires(self, requires):
    """Splits a spec file requires statement.

    The requires statement starts with "Requires: " and is either space or
    comma separated.

    Args:
      requires (str): requires statement.

    Returns:
      list[str]: individual required dependencies, such as "libbde" or
          "liblnk >= 20190520", sorted by name.

    Raises:
      ValueError: if the requires statement does not start with "Requires: ".
    """
    if not requires:
      return []

    if (not requires.startswith('BuildRequires: ') and
        not requires.startswith('Requires: ')):
      raise ValueError(
          'Unsupported requires statement: "{0:s}".'.format(requires))

    _, _, requires = requires.strip().partition(' ')

    # The requires statement can be space or comma separated. If it is space
    # separated we want to keep the name of the requirement and its version
    # grouped together.
    if ',' in requires:
      return sorted([require.strip() for require in requires.split(',')])

    requires_list = []
    requires_segments = [require.strip() for require in requires.split(' ')]
    number_of_segments = len(requires_segments)

    group_start_index = 0
    while group_start_index < number_of_segments:
      group_end_index = group_start_index + 1
      if (group_end_index < number_of_segments and
          requires_segments[group_end_index] in ('>=', '==')):
        group_end_index += 2

      group = ' '.join(requires_segments[group_start_index:group_end_index])
      requires_list.append(group)

      group_start_index = group_end_index

    return sorted(requires_list)

  def _WriteChangeLog(self, output_file_object, version):
    """Writes the change log.

    Args:
      output_file_object (file): output file-like object to write to.
      version (str): version.
    """
    date_time = datetime.datetime.now()
    date_time_string = date_time.strftime('%a %b %e %Y')

    output_file_object.write((
        '%changelog\n'
        '* {0:s} {1:s} {2:s}-1\n'
        '- Auto-generated\n').format(
            date_time_string, self._EMAIL_ADDRESS, version))

  def _WriteDataPackageDefinition(self, output_file_object, configuration):
    """Writes the data package definition.

    Args:
      output_file_object (file): output file-like object to write to.
      configuration (dict[str, str]): package configuration.
    """
    template_mappings = {
        'description': configuration['description'],
        'summary': configuration['summary']}

    output_string = '\n'.join(self._SPEC_TEMPLATE_DATA_PACKAGE_DEFINITION)
    output_string = output_string.format(**template_mappings)
    output_file_object.write(output_string)

  def _WriteDataPackageFiles(self, output_file_object):
    """Writes the data package files.

    Args:
      output_file_object (file): output file-like object to write to.
    """
    template = [
        '%files -n %{name}-data',
        '%defattr(644,root,root,755)',
        '%license LICENSE',
        '%doc ACKNOWLEDGEMENTS AUTHORS README',
        '%{_datadir}/%{name}/*',
        '',
        '']

    output_string = '\n'.join(template)
    output_file_object.write(output_string)

  def _WritePython3Body(self, output_file_object, project_name):
    """Writes the Python 3 body.

    Args:
      output_file_object (file): output file-like object to write to.
      project_name (str): name of the project.
    """
    # TODO: handle GetInstallDefinition

    if project_name == 'psutil':
      name = '%{name}-release-%{version}'
    else:
      name = '%{name}-%{version}'

    template_mappings = {
        'name': name}

    output_string = '\n'.join(self._SPEC_TEMPLATE_PYTHON3_BODY)
    output_string = output_string.format(**template_mappings)
    output_file_object.write(output_string)

  def _WritePython3PackageDefinition(
      self, project_definition, source_directory, python_package_name,
      configuration, output_file_object):
    """Writes the Python 3 package definition.

    Args:
      project_definition (ProjectDefinition): project definition.
      source_directory (str): path of the source directory.
      python_package_name (str): Python package name.
      configuration (dict[str, str]): package configuration.
      output_file_object (file): output file-like object to write to.
    """
    requires = project_definition.rpm_dependencies

    if not requires:
      dependencies_file = os.path.join(source_directory, 'dependencies.ini')
      if os.path.isfile(dependencies_file):
        dependency_helper = dependencies.DependencyHelper(
            dependencies_file=dependencies_file)
        requires = dependency_helper.GetRPMRequires()

    template_mappings = {
        'description': configuration['description'],
        'name': python_package_name,
        'requires': ', '.join(requires),
        'summary': configuration['summary']}

    template = ['%package -n {name:s}']

    if requires:
      template.append('Requires: {requires:s}')

    template.extend([
        'Summary: Python 3 module of {summary:s}',
        '',
        '%description -n {name:s}',
        '{description:s}',
        '',
        ''])

    output_string = '\n'.join(template)
    output_string = output_string.format(**template_mappings)
    output_file_object.write(output_string)

  def _WritePython3PackageFiles(
      self, output_file_object, project_definition, project_name, name,
      license_line, doc_line):
    """Writes the Python 3 package files.

    Args:
      output_file_object (file): output file-like object to write to.
      project_definition (ProjectDefinition): project definition.
      project_name (str): name of the project.
      name (str): package name.
      license_line (str): line containing the license file definition.
      doc_line (str): line containing the document files definition.
    """
    # Note that copr currently fails if %{python3_sitelib} is used.

    if project_definition.setup_name:
      setup_name = project_definition.setup_name
    else:
      setup_name = project_name

    # Python modules names contain "_" instead of "-"
    setup_name = setup_name.replace('-', '_')

    template_mappings = {
        'doc': doc_line.rstrip(),
        'license': license_line.rstrip(),
        'name': name,
        'setup_name': setup_name}

    template = [
        '%files -n {name:s}',
        '{license:s}',
        '{doc:s}']

    if project_definition.architecture_dependent:
      template.extend([
          '%{{_libdir}}/python3*/site-packages/{setup_name:s}',
          '%{{_libdir}}/python3*/site-packages/{setup_name:s}*.dist-info'])

    else:
      template.extend([
          '%{{python3_sitelib}}/{setup_name:s}',
          '%{{python3_sitelib}}/{setup_name:s}*.dist-info'])

    template.extend(['', ''])

    output_string = '\n'.join(template)
    output_string = output_string.format(**template_mappings)
    output_file_object.write(output_string)

  def _WriteSpecFileFromTempate(
      self, project_definition, source_directory, project_version,
      output_file_object):
    """Writes the RPM spec file from a template.

    Args:
      project_definition (ProjectDefinition): project definition.
      source_directory (str): path of the source directory.
      project_version (str): project version.
      output_file_object (file): output file-like object to write to.

    Returns:
      bool: True if successful, False otherwise.
    """
    date_time = datetime.datetime.now()
    date_time_string = date_time.strftime('%a %b %e %Y')

    rpm_requires = []

    dependencies_file = os.path.join(source_directory, 'dependencies.ini')
    if os.path.isfile(dependencies_file):
      dependency_helper = dependencies.DependencyHelper(
          dependencies_file=dependencies_file)
      rpm_requires = dependency_helper.GetRPMRequires()

    template_values = {
        'date_time': date_time_string,
        'rpm_requires': ', '.join(rpm_requires),
        'version': project_version}

    template_file_path = os.path.join(
        self._data_path, 'rpm_templates', project_definition.rpm_template_spec)
    with open(template_file_path, 'r', encoding='utf8') as file_object:
      rules_template = file_object.read()

    data = rules_template.format(**template_values)

    output_file_object.write(data)

    return True

  def _WriteSourcePackageDefinition(
      self, output_file_object, source_package_filename, project_definition,
      build_requires, configuration):
    """Writes the source package definition.

    Args:
      output_file_object (file): output file-like object to write to.
      source_package_filename (str): name of the package source file.
      project_definition (ProjectDefinition): project definition.
      build_requires (list[str]): package build requires definition.
      configuration (dict[str, str]): package configuration.
    """
    if source_package_filename.endswith('.zip'):
      source_extension = 'zip'
    else:
      source_extension = 'tar.gz'

    template_mappings = {
        'build_requires': ', '.join(build_requires),
        'description': configuration['description'],
        'group': 'Development/Libraries',
        'license': configuration['license'],
        'name': configuration['name'],
        'source': f'%{{name}}-%{{version}}.{source_extension:s}',
        'summary': configuration['summary'],
        'url': configuration['url'],
        'vendor': configuration['vendor'],
        'version': configuration['version']}

    template = [
        'Name: {name:s}',
        'Version: {version:s}',
        'Release: 1',
        'Group: {group:s}',
        'License: {license:s}',
        'Summary: {summary:s}',
        'Url: {url:s}',
        'Vendor: {vendor:s}']

    template.append('Source0: {source:s}')

    if not project_definition.architecture_dependent:
      template.append('BuildArch: noarch')

    if build_requires:
      template.append('BuildRequires: {build_requires:s}')

    template.extend([
        '',
        '%{{?python_disable_dependency_generator}}',
        '',
        '%description',
        '{description:s}',
        '',
        ''])

    output_string = '\n'.join(template)
    output_string = output_string.format(**template_mappings)
    output_file_object.write(output_string)

  def _WriteToolsPackageDefinition(self, output_file_object, configuration):
    """Writes the tools package definition.

    Args:
      output_file_object (file): output file-like object to write to.
      configuration (dict[str, str]): package configuration.
    """
    template_mappings = {
        'description': configuration['description'],
        'project_name': configuration['name'],
        'summary': configuration['summary']}

    output_string = '\n'.join(self._SPEC_TEMPLATE_TOOLS_PACKAGE_DEFINITION)
    output_string = output_string.format(**template_mappings)
    output_file_object.write(output_string)

  def _WriteToolsPackageFiles(self, output_file_object):
    """Writes the tools package files.

    Args:
      output_file_object (file): output file-like object to write to.
    """
    output_file_object.write(
        '%files -n %{name}-tools\n'
        '%{_bindir}/*\n'
        '\n')

  def Generate(
      self, project_definition, source_directory, source_package_filename,
      project_name, project_version, output_file):
    """Generated a RPM spec file.

    Args:
      project_definition (ProjectDefinition): project definition.
      source_directory (str): path of the source directory.
      source_package_filename (str): name of the source package.
      project_name (str): name of the project.
      project_version (str): version of the project.
      output_file (str): path of the output RPM spec file.

    Returns:
      bool: True if successful, False otherwise.
    """
    rpm_build_dependencies = [
        'python3-devel', 'pyproject-rpm-macros', 'python3-pip',
        'python3-setuptools', 'python3-wheel']

    if project_definition.architecture_dependent:
      rpm_build_dependencies.append('gcc')

    if project_definition.rpm_build_dependencies:
      rpm_build_dependencies.extend(project_definition.rpm_build_dependencies)

    with open(output_file, 'w', encoding='utf8') as output_file_object:
      if project_definition.rpm_template_spec:
        result = self._WriteSpecFileFromTempate(
            project_definition, source_directory, project_version,
            output_file_object)
      else:
        result = self._GenerateSpecFile(
            project_definition, source_directory, source_package_filename,
            project_name, rpm_build_dependencies, output_file_object)

    return result
