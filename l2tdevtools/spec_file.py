# -*- coding: utf-8 -*-
"""RPM spec file generator."""

import datetime
import logging
import io
import os
import subprocess
import sys


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
      '{description:s}']

  _SPEC_TEMPLATE_PYTHON3_BODY = [
      '%prep',
      '%autosetup -n {name:s}',
      '',
      '%build',
      '%py3_build',
      '',
      '%install',
      '%py3_install',
      ('rm -rf %{{buildroot}}/usr/lib/python*/site-packages/*.egg-info/'
       'requires.txt'),
      'rm -rf %{{buildroot}}/usr/share/doc/%{{name}}/',
      '',
      '%clean',
      'rm -rf %{{buildroot}}',
      '',
      '']

  _SPEC_TEMPLATE_TOOLS_PACKAGE_DEFINITION = [
      '%package -n %{{name}}-tools',
      'Requires: python3-{project_name:s} >= %{{version}}',
      'Summary: Tools for {summary:s}',
      '',
      '%description -n %{{name}}-tools',
      '{description:s}']

  def __init__(self, data_path):
    """Initializes the RPM spec file generator.

    Args:
      data_path (str): path to the data directory which contains the RPM
          templates and patches sub directories.
    """
    super(RPMSpecFileGenerator, self).__init__()
    self._data_path = data_path

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

    doc_file_definition = ''
    if doc_files:
      doc_file_definition = '%doc {0:s}\n'.format(' '.join(doc_files))

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
        ('rm -rf %{buildroot}/usr/lib/python*/site-packages/*.egg-info/'
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

  def _GetPython3Requires(self, requires):
    """Determines the Python 3 requires definition.

    Args:
      requires (str): requires definition.

    Returns:
      list[str]: Python 3 requires definition.
    """
    requires = requires.replace('-python2 ', '-python3 ')
    requires = requires.replace('-python ', '-python3 ')
    requires = requires.replace(' python2-', ' python3-')
    requires = requires.replace(' python-', ' python3-')

    # Remove Python 2 only dependencies like backports or pysqlite.
    return [require for require in self._SplitRequires(requires)
            if 'backports' not in require and 'pysqlite' not in require]

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

  def _WriteDataPackageDefinition(
      self, output_file_object, summary, description):
    """Writes the data package definition.

    Args:
      output_file_object (file): output file-like object to write to.
      summary (str): package summary.
      description (str): package description.
    """
    template_mappings = {
        'description': description,
        'summary': summary}

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

  def _WriteHeader(
      self, output_file_object, project_name, unmangled_name, version):
    """Writes the header.

    Args:
      output_file_object (file): output file-like object to write to.
      project_name (str): name of the project.
      unmangled_name (str): unmangled name of the project.
      version (str): version.
    """
    template_mappings = {
        'name': project_name,
        'unmangled_name': unmangled_name,
        'version': version}

    template = [
        '%define name {name:s}',
        '%define version {version:s}']

    if unmangled_name:
      template.extend([
          '%define unmangled_name {unmanged_name:s}',
          '%define unmangled_version {version:s}'])

    template.extend([
        '%define release 1',
        '',
        ''])

    output_string = '\n'.join(template)
    output_string = output_string.format(**template_mappings)
    output_file_object.write(output_string)

  def _WritePython3Body(self, output_file_object, project_name, unmangled_name):
    """Writes the Python 3 body.

    Args:
      output_file_object (file): output file-like object to write to.
      project_name (str): name of the project.
      unmangled_name (str): unmangled name of the project.
    """
    # TODO: handle GetInstallDefinition

    if project_name == 'psutil':
      name = '%{name}-release-%{version}'
    elif unmangled_name:
      name = '%{unmangled_name}-%{unmangled_version}'
    else:
      name = '%{name}-%{version}'

    template_mappings = {
        'name': name}

    output_string = '\n'.join(self._SPEC_TEMPLATE_PYTHON3_BODY)
    output_string = output_string.format(**template_mappings)
    output_file_object.write(output_string)

  def _WritePython3PackageDefinition(
      self, output_file_object, name, summary, requires, description):
    """Writes the Python 3 package definition.

    Args:
      output_file_object (file): output file-like object to write to.
      name (str): package name.
      summary (str): package summary.
      requires (list[str]): package requires definition.
      description (str): package description.
    """
    template_mappings = {
        'description': description,
        'name': name,
        'requires': ', '.join(requires),
        'summary': summary}

    template = ['%package -n {name:s}']

    if requires:
      template.append('Requires: {requires:s}')

    template.extend([
        'Summary: Python 3 module of {summary:s}',
        '',
        '%description -n {name:s}',
        '{description:s}'])

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
          '%{{_libdir}}/python3*/site-packages/{setup_name:s}*.egg-info'])

    else:
      template.extend([
          '%{{python3_sitelib}}/{setup_name:s}',
          '%{{python3_sitelib}}/{setup_name:s}*.egg-info'])

    template.extend(['', ''])

    output_string = '\n'.join(template)
    output_string = output_string.format(**template_mappings)
    output_file_object.write(output_string)

  # pylint: disable=too-many-arguments
  def _WriteSourcePackageDefinition(
      self, output_file_object, source_filename, project_definition,
      unmangled_name, summary, package_license, url, packager, vendor,
      build_requires, description):
    """Writes the source package definition.

    Args:
      output_file_object (file): output file-like object to write to.
      source_filename (str): name of the package source file.
      project_definition (ProjectDefinition): project definition.
      unmangled_name (str): unmangled name of the project.
      summary (str): package summary.
      package_license (str): package license.
      url (str): package URL.
      packager (str): packager.
      vendor (str): vendor.
      build_requires (list[str]): package build requires definition.
      description (str): package description.
    """
    if source_filename.endswith('.zip'):
      source_extension = 'zip'
    else:
      source_extension = 'tar.gz'

    if unmangled_name:
      source = '%{{unmangled_name}}-%{{unmangled_version}}.{0:s}'.format(
          source_extension)
    else:
      source = '%{{name}}-%{{version}}.{0:s}'.format(source_extension)

    if unmangled_name:
      build_root = (
          '%{_tmppath}/%{unmangled_name}-%{version}-%{release}-buildroot')
    else:
      build_root = '%{_tmppath}/%{name}-%{version}-%{release}-buildroot'

    template_mappings = {
        'build_root': build_root,
        'build_requires': ', '.join(build_requires),
        'description': description,
        'group': 'Development/Libraries',
        'license': package_license,
        'packager': packager,
        'source': source,
        'summary': summary,
        'url': url,
        'vendor': vendor}

    template = [
        'Summary: {summary:s}',
        'Name: %{{name}}',
        'Version: %{{version}}',
        'Release: %{{release}}',
        'Source0: {source:s}',
        'License: {license:s}',
        'Group: {group:s}',
        'BuildRoot: {build_root:s}',
        'Prefix: %{{_prefix}}']

    if not project_definition.architecture_dependent:
      template.append('BuildArch: noarch')

    template.append('Vendor: {vendor:s}')

    if packager:
      template.append('Packager: {packager:s}')

    template.append('Url: {url:s}')

    if build_requires:
      template.append('BuildRequires: {build_requires:s}')

    template.extend([
        '',
        '%description',
        '{description:s}'])

    output_string = '\n'.join(template)
    output_string = output_string.format(**template_mappings)
    output_file_object.write(output_string)

  def _WriteToolsPackageDefinition(
      self, output_file_object, project_name, summary, description):
    """Writes the tools package definition.

    Args:
      output_file_object (file): output file-like object to write to.
      project_name (str): name of the project.
      summary (str): package summary.
      description (str): package description.
    """
    template_mappings = {
        'description': description,
        'project_name': project_name,
        'summary': summary}

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
        '%{_bindir}/*.py\n'
        '\n')

  def GenerateWithSetupPy(self, source_directory, build_log_file):
    """Generates the RPM spec file with setup.py.

    Args:
      source_directory (str): path of the source directory.
      build_log_file (str): path of the build log file.

    Returns:
      bool: True if successful, False otherwise.
    """
    command = '{0:s} setup.py bdist_rpm --spec-only >> {1:s} 2>&1'.format(
        sys.executable, build_log_file)
    exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _RewriteSetupPyGeneratedFile(
      self, project_definition, source_directory, source_filename,
      project_name, rpm_build_dependencies, input_file, output_file_object):
    """Rewrites the RPM spec file generated with setup.py.

    Args:
      project_definition (ProjectDefinition): project definition.
      source_directory (str): path of the source directory.
      source_filename (str): name of the source package.
      project_name (str): name of the project.
      rpm_build_dependencies (list[str]): RPM build dependencies.
      input_file (str): path of the input RPM spec file.
      output_file_object (file): output file-like object to write to.

    Returns:
      bool: True if successful, False otherwise.
    """
    project_version = ''
    description = ''
    package_license = ''
    packager = ''
    requires = ''
    summary = ''
    url = ''
    vendor = ''
    build_requires = ''
    python_package_requires = ''

    has_data_package = False
    has_tools_package = False

    in_description = False
    in_python_package = False

    if project_definition.rpm_name:
      package_name = project_definition.rpm_name
    else:
      package_name = project_name

    if package_name.startswith('python-'):
      package_name = package_name[7:]

    unmangled_name = ''
    if package_name != project_name:
      unmangled_name = project_name

    with io.open(input_file, 'r+', encoding='utf8') as input_file_object:
      for line in input_file_object.readlines():
        if in_description:
          if line.startswith('%'):
            in_description = False

          elif not description and line == '\n':
            # Ignore leading white lines in the description.
            continue

          else:
            description = ''.join([description, line])

        if in_python_package:
          if line.startswith('%package') or line.startswith('%prep'):
            in_python_package = False

          elif not python_package_requires and line.startswith('Requires: '):
            python_package_requires = line

        if in_description or in_python_package:
          continue

        if line.startswith('%define version '):
          _, _, project_version = line.strip().rpartition(' ')

        elif line.startswith('BuildRequires: '):
          build_requires = line

        elif not package_license and line.startswith('License: '):
          _, _, package_license = line.strip().partition(' ')

        elif not packager and line.startswith('Packager: '):
          _, _, packager = line.strip().partition(' ')

        elif not summary and line.startswith('Summary: '):
          _, _, summary = line.strip().partition(' ')

        elif not url and line.startswith('Url: '):
          _, _, url = line.strip().partition(' ')

        elif not vendor and line.startswith('Vendor: '):
          _, _, vendor = line.strip().partition(' ')

        elif (not description and not requires and
              line.startswith('Requires: ')):
          requires = line

        elif line.startswith('%description') and not description:
          in_description = True

        elif line.startswith('%package -n %{name}-data'):
          has_data_package = True

        elif line.startswith('%package -n %{name}-tools'):
          has_tools_package = True

        elif (line.startswith('%package -n python-') or
              line.startswith('%package -n python2-') or
              line.startswith('%package -n python3-')):
          in_python_package = True

        elif line.startswith('%files'):
          break

    self._WriteHeader(
        output_file_object, project_name, unmangled_name, project_version)

    if project_definition.description_long:
      description = '{0:s}\n\n'.format(project_definition.description_long)

    if rpm_build_dependencies:
      build_requires = rpm_build_dependencies
    else:
      build_requires = self._SplitRequires(build_requires)

    self._WriteSourcePackageDefinition(
        output_file_object, source_filename, project_definition, unmangled_name,
        summary, package_license, url, packager, vendor, build_requires,
        description)

    if project_name != package_name:
      python_package_name = 'python3-{0:s}'.format(package_name)
    else:
      python_package_name = 'python3-%{name}'

    python3_requires = python_package_requires
    if not python3_requires:
      python3_requires = requires

    python3_requires = self._GetPython3Requires(python3_requires)

    if has_data_package:
      self._WriteDataPackageDefinition(
          output_file_object, summary, description)

    self._WritePython3PackageDefinition(
        output_file_object, python_package_name, summary,
        python3_requires, description)

    if has_tools_package:
      self._WriteToolsPackageDefinition(
          output_file_object, project_name, summary, description)

    license_line = self._GetLicenseFileDefinition(source_directory)

    doc_line = self._GetDocumentationFilesDefinition(source_directory)

    self._WritePython3Body(output_file_object, project_name, unmangled_name)

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

    if project_name == 'dfvfs':
      output_file_object.write((
          '%exclude %{python3_sitelib}/examples\n'
          '\n'))

    self._WriteChangeLog(output_file_object, project_version)

    return True

  def _RewriteSetupPyGeneratedFileForOSC(
      self, input_file_object, output_file_object):
    """Rewrites the RPM spec file generated with setup.py for OSC.

    Args:
      input_file_object (file): input file-like object to read from.
      output_file_object (file): output file-like object to write to.

    Returns:
      bool: True if successful, False otherwise.
    """
    for line in input_file_object.readlines():
      output_file_object.write(line)

    return True

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

  def _WriteSpecFileFromTempate(
      self, template_filename, project_version, output_file_object):
    """Writes the RPM spec file from a template.

    Args:
      template_filename (str): name of the template file.
      project_version (str): project version.
      output_file_object (file): output file-like object to write to.

    Returns:
      bool: True if successful, False otherwise.
    """
    date_time = datetime.datetime.now()
    date_time_string = date_time.strftime('%a %b %e %Y')

    template_values = {
        'date_time': date_time_string,
        'version': project_version}

    template_file_path = os.path.join(
        self._data_path, 'rpm_templates', template_filename)
    with io.open(template_file_path, 'r', encoding='utf8') as file_object:
      rules_template = file_object.read()

    data = rules_template.format(**template_values)

    output_file_object.write(data)

    return True

  def RewriteSetupPyGeneratedFile(
      self, project_definition, source_directory, source_filename,
      project_name, project_version, input_file, output_file):
    """Rewrites the RPM spec file generated with setup.py.

    Args:
      project_definition (ProjectDefinition): project definition.
      source_directory (str): path of the source directory.
      source_filename (str): name of the source package.
      project_name (str): name of the project.
      project_version (str): version of the project.
      input_file (str): path of the input RPM spec file.
      output_file (str): path of the output RPM spec file.

    Returns:
      bool: True if successful, False otherwise.
    """
    rpm_build_dependencies = []

    if project_definition.architecture_dependent:
      rpm_build_dependencies = ['gcc', 'python3-devel', 'python3-setuptools']
    else:
      rpm_build_dependencies = ['python3-devel', 'python3-setuptools']

    if project_definition.rpm_build_dependencies:
      rpm_build_dependencies.extend(project_definition.rpm_build_dependencies)

    # TODO: check if already prefixed with python-

    with io.open(output_file, 'w', encoding='utf8') as output_file_object:
      if project_definition.rpm_template_spec:
        result = self._WriteSpecFileFromTempate(
            project_definition.rpm_template_spec, project_version,
            output_file_object)
      else:
        result = self._RewriteSetupPyGeneratedFile(
            project_definition, source_directory, source_filename,
            project_name, rpm_build_dependencies, input_file,
            output_file_object)

    return result

  def RewriteSetupPyGeneratedFileForOSC(self, spec_file_path):
    """Rewrites the RPM spec file generated with setup.py for OSC.

    Args:
      spec_file_path (str): path of the RPM spec file.

    Returns:
      bool: True if successful, False otherwise.
    """
    with io.StringIO() as temporary_file_object:
      with io.open(spec_file_path, 'r', encoding='utf8') as input_file_object:
        data = input_file_object.read()
        temporary_file_object.write(data)

      temporary_file_object.seek(0, os.SEEK_SET)

      with io.open(spec_file_path, 'w', encoding='utf8') as output_file_object:
        result = self._RewriteSetupPyGeneratedFileForOSC(
            temporary_file_object, output_file_object)

    return result
