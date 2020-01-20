# -*- coding: utf-8 -*-
"""RPM spec file generator."""

from __future__ import unicode_literals

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

  def __init__(self, data_path):
    """Initializes the RPM spec file generator.

    Args:
      data_path (str): path to the data directory which contains the RPM
          templates and patches sub directories.
    """
    super(RPMSpecFileGenerator, self).__init__()
    self._data_path = data_path

  def _GetBuildDefinition(self):
    """Retrieves the build definition.

    Returns:
      str: build definition.
    """
    return '\n'.join(['%py2_build', '%py3_build', ''])

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
        '%py2_install',
        '%py3_install',
        'rm -rf %{buildroot}/usr/share/doc/%{name}/']

    if project_name == 'astroid':
      lines.extend([
          'rm -rf %{buildroot}%{python2_sitelib}/astroid/tests',
          'rm -rf %{buildroot}%{python3_sitelib}/astroid/tests'])

    elif project_name == 'pylint':
      lines.extend([
          'rm -rf %{buildroot}%{python2_sitelib}/pylint/test',
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

  def _GetPython2Requires(self, requires):
    """Determines the Python 2 requires definition.

    Args:
      requires (str): requires definition.

    Returns:
      list[str]: Python 2 requires definition.
    """
    requires = requires.replace('-python3 ', '-python2 ')
    requires = requires.replace('-python ', '-python2 ')
    requires = requires.replace(' python3-', ' python2-')
    requires = requires.replace(' python-', ' python2-')

    return self._SplitRequires(requires)

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
    return [
        require for require in self._SplitRequires(requires)
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
        '\n'
        '%changelog\n'
        '* {0:s} {1:s} {2:s}-1\n'
        '- Auto-generated\n').format(
            date_time_string, self._EMAIL_ADDRESS, version))

  def _WritePython2PackageDefinition(
      self, output_file_object, name, summary, requires, description):
    """Writes the Python 2 package definition.

    Args:
      output_file_object (file): output file-like object to write to.
      name (str): package name.
      summary (str): package summary.
      requires (list[str]): package requires definition.
      description (str): package description.
    """
    output_file_object.write('%package -n {0:s}\n'.format(name))
    if name == 'pytz':
      output_file_object.write(
          'Obsoletes: %{name} < %{version}\n'
          'Provides: %{name} = %{version}\n')
    else:
      output_file_object.write(
          'Obsoletes: python-%{name} < %{version}\n'
          'Provides: python-%{name} = %{version}\n')

    if requires:
      output_file_object.write('Requires: {0:s}\n'.format(', '.join(requires)))

    output_file_object.write((
        '{0:s}'
        '\n'
        '%description -n {1:s}\n'
        '{2:s}').format(summary, name, description))

  def _WritePython2PackageFiles(
      self, output_file_object, project_definition, project_name, name,
      license_line, doc_line):
    """Writes the Python 2 package files.

    Args:
      output_file_object (file): output file-like object to write to.
      project_definition (ProjectDefinition): project definition.
      project_name (str): name of the project.
      name (str): package name.
      license_line (str): line containing the license file definition.
      doc_line (str): line containing the document files definition.
    """
    # Note that copr currently fails if %{python2_sitelib} is used.

    if project_definition.setup_name:
      setup_name = project_definition.setup_name
    else:
      setup_name = project_name

    # Python modules names contain "_" instead of "-"
    setup_name = setup_name.replace('-', '_')

    # TODO: replace hardcoded exception for templates
    if project_name == 'pefile':
      output_file_object.write((
          '%files -n {0:s}\n'
          '{1:s}'
          '{2:s}'
          '%{{python2_sitelib}}/\n').format(
              name, license_line, doc_line))

    elif project_name == 'pytsk3':
      output_file_object.write((
          '%files -n {0:s}\n'
          '{1:s}'
          '{2:s}'
          '%{{_libdir}}/python2*/site-packages/{3:s}*.so\n'
          '%{{_libdir}}/python2*/site-packages/{3:s}*.egg-info\n').format(
              name, license_line, doc_line, setup_name))

    elif project_definition.architecture_dependent:
      output_file_object.write((
          '%files -n {0:s}\n'
          '{1:s}'
          '{2:s}'
          '%{{_libdir}}/python2*/site-packages/{3:s}\n'
          '%{{_libdir}}/python2*/site-packages/{3:s}*.egg-info\n').format(
              name, license_line, doc_line, setup_name))

    else:
      output_file_object.write((
          '%files -n {0:s}\n'
          '{1:s}'
          '{2:s}'
          '%{{python2_sitelib}}/{3:s}\n'
          '%{{python2_sitelib}}/{3:s}*.egg-info\n').format(
              name, license_line, doc_line, setup_name))

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
    output_file_object.write('%package -n {0:s}\n'.format(name))

    if requires:
      output_file_object.write('Requires: {0:s}\n'.format(', '.join(requires)))

    output_file_object.write((
        '{0:s}'
        '\n'
        '%description -n {1:s}\n'
        '{2:s}').format(summary, name, description))

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

    # TODO: replace hard coding one-offs with templates.
    if project_name == 'pefile':
      output_file_object.write((
          '\n'
          '%files -n {0:s}\n'
          '{1:s}'
          '{2:s}'
          '%{{python3_sitelib}}/\n').format(
              name, license_line, doc_line))

    elif project_name == 'pytsk3':
      output_file_object.write((
          '\n'
          '%files -n {0:s}\n'
          '{1:s}'
          '{2:s}'
          '%{{_libdir}}/python3*/site-packages/{3:s}*.so\n'
          '%{{_libdir}}/python3*/site-packages/{3:s}*.egg-info\n').format(
              name, license_line, doc_line, setup_name))

    elif project_definition.architecture_dependent:
      output_file_object.write((
          '\n'
          '%files -n {0:s}\n'
          '{1:s}'
          '{2:s}'
          '%{{_libdir}}/python3*/site-packages/{3:s}\n'
          '%{{_libdir}}/python3*/site-packages/{3:s}*.egg-info\n').format(
              name, license_line, doc_line, setup_name))

    else:
      output_file_object.write((
          '\n'
          '%files -n {0:s}\n'
          '{1:s}'
          '{2:s}'
          '%{{python3_sitelib}}/{3:s}\n'
          '%{{python3_sitelib}}/{3:s}*.egg-info\n').format(
              name, license_line, doc_line, setup_name))

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
      project_name, rpm_build_dependencies, input_file, output_file_object,
      python2_package_prefix='python2-'):
    """Rewrites the RPM spec file generated with setup.py.

    Args:
      project_definition (ProjectDefinition): project definition.
      source_directory (str): path of the source directory.
      source_filename (str): name of the source package.
      project_name (str): name of the project.
      rpm_build_dependencies (list[str]): RPM build dependencies.
      input_file (str): path of the input RPM spec file.
      output_file_object (file): output file-like object to write to.
      python2_package_prefix (Optional[str]): name prefix for Python 2 packages.

    Returns:
      bool: True if successful, False otherwise.
    """
    description = ''
    requires = ''
    summary = ''
    version = ''
    python_requires = ''

    in_description = False
    in_python_package = False
    has_build_requires = False
    has_python2_package = False
    has_python3_package = False
    has_unmangled_version = False

    generated_build_definition = False
    generated_install_definition = False

    if project_definition.rpm_name:
      package_name = project_definition.rpm_name
    else:
      package_name = project_name

    if package_name.startswith('python-'):
      package_name = package_name[7:]

    unmangled_name = project_name

    with io.open(input_file, 'r+', encoding='utf8') as input_file_object:
      for line in input_file_object.readlines():
        if line.startswith('%') and in_description:
          in_description = False

          if project_definition.description_long:
            description = '{0:s}\n\n'.format(
                project_definition.description_long)

          output_file_object.write(description)

        if line.startswith('%prep') and in_python_package:
          in_python_package = False

        if in_python_package and project_name == 'plaso':
          continue

        if line.startswith('%define name '):
          # Need to override the project name for projects that prefix
          # their name with "python-" (or equivalent) in setup.py but
          # do not use it for their source package name.
          line = '%define name {0:s}\n'.format(project_name)

        elif line.startswith('%define version '):
          version = line[16:-1]
          if version.startswith('1!'):
            version = version[2:]

        elif line.startswith('%define unmangled_version '):
          # setup.py generates %define unmangled_version twice ignore
          # the second define.
          if has_unmangled_version:
            continue

          output_file_object.write(
              '%define unmangled_name {0:s}\n'.format(unmangled_name))

          has_unmangled_version = True

        elif not summary and line.startswith('Summary: '):
          summary = line

        elif line.startswith('Source0: '):
          if source_filename.endswith('.zip'):
            line = 'Source0: %{unmangled_name}-%{unmangled_version}.zip\n'
          else:
            line = 'Source0: %{unmangled_name}-%{unmangled_version}.tar.gz\n'

        elif line.startswith('BuildRoot: '):
          if project_name == 'psutil':
            line = (
                'BuildRoot: %{_tmppath}/'
                '%{name}-release-%{version}-%{release}-buildroot\n')

          else:
            line = (
                'BuildRoot: %{_tmppath}/'
                '%{unmangled_name}-release-%{version}-%{release}-buildroot\n')

        elif (not description and not requires and
              line.startswith('Requires: ')):
          requires = line
          continue

        elif (in_python_package and not python_requires and
              line.startswith('Requires: ')):
          original_line = line

          if has_python2_package:
            python_requires = self._GetPython2Requires(line)
          elif has_python3_package:
            python_requires = self._GetPython3Requires(line)
          else:
            python_requires = self._SplitRequires(line)

          if python_requires:
            line = 'Requires: {0:s}\n'.format(', '.join(python_requires))

          python_requires = original_line

        elif line.startswith('BuildArch: noarch'):
          if project_definition.architecture_dependent:
            continue

        elif line.startswith('BuildRequires: '):
          has_build_requires = True
          line = 'BuildRequires: {0:s}\n'.format(', '.join(
              rpm_build_dependencies))

        elif line == '\n' and summary and not has_build_requires:
          has_build_requires = True
          line = 'BuildRequires: {0:s}\n\n'.format(', '.join(
              rpm_build_dependencies))

        elif line.startswith('%description') and not description:
          in_description = True

        elif (line.startswith('%package -n python-') or
              line.startswith('%package -n python2-')):
          in_python_package = not python_requires
          has_python2_package = True

          if line.startswith('%package -n python2-'):
            if python2_package_prefix == 'python-':
              logging.warning(
                  'rpm_python_package prefix is: "python" but spec file '
                  'defines: "python2"')
            python2_package_prefix = 'python2-'

        elif line.startswith('%package -n python3-'):
          in_python_package = not python_requires
          has_python3_package = True

        elif line.startswith('%prep'):
          if project_name == 'plaso':
            requires = '{0:s}, {1:s}-data\n'.format(
                requires[:-1], project_name)

          if not has_python2_package:
            if project_name != package_name:
              python_package_name = '{0:s}{1:s}'.format(
                  python2_package_prefix, package_name)
            else:
              python_package_name = '{0:s}%{{name}}'.format(
                  python2_package_prefix)

            if python_package_name != '%{name}':
              python2_requires = python_requires
              if not python2_requires:
                python2_requires = requires

              python2_requires = self._GetPython2Requires(python2_requires)
              self._WritePython2PackageDefinition(
                  output_file_object, python_package_name, summary,
                  python2_requires, description)

          if not has_python3_package:
            if project_name != package_name:
              python_package_name = 'python3-{0:s}'.format(package_name)
            else:
              python_package_name = 'python3-%{name}'

            python3_requires = python_requires
            if not python3_requires:
              python3_requires = requires

            python3_requires = self._GetPython3Requires(python3_requires)
            self._WritePython3PackageDefinition(
                output_file_object, python_package_name, summary,
                python3_requires, description)

          if project_name == 'plaso':
            output_file_object.write((
                '%package -n %{{name}}-data\n'
                '{0:s}'
                '\n'
                '%description -n %{{name}}-data\n'
                '{1:s}').format(summary, description))

        elif line.startswith('%setup -n %{name}-%{unmangled_version}'):
          if project_name == 'psutil':
            line = '%autosetup -n %{name}-release-%{unmangled_version}\n'
          else:
            line = '%autosetup -n %{unmangled_name}-%{unmangled_version}\n'

        elif (line.startswith('python setup.py build') or
              line.startswith('python2 setup.py build') or
              line.startswith('python3 setup.py build') or
              line.startswith('%py2_build') or line.startswith('%py3_build') or
              line.startswith(
                  'env CFLAGS="$RPM_OPT_FLAGS" python setup.py build') or
              line.startswith(
                  'env CFLAGS="$RPM_OPT_FLAGS" python3 setup.py build')):
          if not generated_build_definition:
            line = self._GetBuildDefinition()
            generated_build_definition = True

        elif (line.startswith('python setup.py install') or
              line.startswith('python2 setup.py install') or
              line.startswith('python3 setup.py install') or
              line.startswith('%py2_install') or
              line.startswith('%py3_install')):
          if not generated_install_definition:
            line = self._GetInstallDefinition(project_name)
            generated_install_definition = True

        elif line == 'rm -rf $RPM_BUILD_ROOT\n':
          line = 'rm -rf %{buildroot}\n'

        elif (line.startswith('%files') and
              not line.startswith('%files -n %{name}-data')):
          break

        elif in_description:
          # Ignore leading white lines in the description.
          if not description and line == '\n':
            continue

          description = ''.join([description, line])
          continue

        output_file_object.write(line)

    license_line = self._GetLicenseFileDefinition(source_directory)

    doc_line = self._GetDocumentationFilesDefinition(source_directory)

    if project_name != package_name:
      python_package_name = '{0:s}{1:s}'.format(
          python2_package_prefix, package_name)
    else:
      python_package_name = '{0:s}%{{name}}'.format(python2_package_prefix)

    self._WritePython2PackageFiles(
        output_file_object, project_definition, project_name,
        python_package_name, license_line, doc_line)

    if project_name != package_name:
      python_package_name = 'python3-{0:s}'.format(package_name)
    else:
      python_package_name = 'python3-%{name}'

    self._WritePython3PackageFiles(
        output_file_object, project_definition, project_name,
        python_package_name, license_line, doc_line)

    if project_name == 'plaso':
      output_file_object.write(
          '\n'
          '%files -n %{name}-data\n'
          '%{_datadir}/%{name}/*\n')

    # TODO: add bindir support.
    output_file_object.write((
        '\n'
        '%exclude %{_bindir}/*\n'))

    # TODO: add shared data support.

    self._WriteChangeLog(output_file_object, version)

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
    in_python3_package = False

    for line in input_file_object.readlines():
      if in_python3_package and (
          line.startswith('%changelog') or line.startswith('%exclude ') or
          line.startswith('%files ') or line.startswith('%package ') or
          line.startswith('%prep')):

        if line.startswith('%exclude %{python3_sitelib}'):
          output_file_object.write(line)
          continue

        output_file_object.write('%endif # %{defined fedora} >= 28\n')
        output_file_object.write('\n')

        in_python3_package = False

      elif (not in_python3_package and line.startswith('BuildRequires: ') and
            'python' in line):
        build_requires = [require.strip() for require in line[15:].split(',')]
        python_build_requires = [
            require.strip() for require in build_requires
            if 'python3' not in require]

        output_file_object.write('%if %{defined fedora} >= 28\n')
        output_file_object.write('BuildRequires: {0:s}\n'.format(', '.join(
            build_requires)))
        output_file_object.write('%else\n')
        output_file_object.write('BuildRequires: {0:s}\n'.format(', '.join(
            python_build_requires)))
        output_file_object.write('%endif\n')
        continue

      elif line.startswith('%files -n python3-') or (
          line.startswith('%files -n ') and line.endswith('-python3\n')):
        output_file_object.write('%if %{defined fedora} >= 28\n')
        output_file_object.write('\n')

        in_python3_package = True

      elif line.startswith('%package -n python3-') or (
          line.startswith('%package -n ') and line.endswith('-python3\n')):
        output_file_object.write('%if %{defined fedora} >= 28\n')
        output_file_object.write('\n')

        in_python3_package = True

      elif line.startswith('%py3_build') or line.startswith('%py3_install'):
        output_file_object.write('%if %{defined fedora} >= 28\n')
        output_file_object.write(line)
        output_file_object.write('%endif\n')
        continue

      elif (line.startswith('%configure ') and
            '--enable-python2 --enable-python3' in line):
        output_file_object.write('%if %{defined fedora} >= 28\n')
        output_file_object.write(line)
        output_file_object.write('%else\n')
        line = line.replace(
            '--enable-python2 --enable-python3', '--enable-python')
        output_file_object.write(line)
        output_file_object.write('%endif\n')
        continue

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

    if not requires.startswith('Requires: '):
      raise ValueError(
          'Unsupported requires statement: "{0:s}".'.format(requires))

    # The requires statement can be space or comma separated. If it is space
    # separated we want to keep the name of the requirement and its version
    # grouped together.
    if ',' in requires:
      return sorted([require.strip() for require in requires[10:].split(',')])

    requires_list = []
    requires_segments = [
        require.strip() for require in requires[10:].split(' ')]
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
    if project_name in ('lz4', 'psutil', 'pysqlite', 'yara-python'):
      rpm_build_dependencies = ['gcc']

    elif project_name == 'pytsk3':
      rpm_build_dependencies = ['gcc', 'gcc-c++', 'libstdc++-devel']

    elif project_name == 'pyzmq':
      rpm_build_dependencies = ['gcc', 'gcc-c++']

    else:
      rpm_build_dependencies = []

    rpm_build_dependencies.extend(['python2-setuptools', 'python2-devel'])

    if project_definition.rpm_build_dependencies:
      rpm_build_dependencies.extend(project_definition.rpm_build_dependencies)

    rpm_build_dependencies.extend(['python3-setuptools', 'python3-devel'])

    if project_definition.rpm_build_dependencies:
      for dependency in project_definition.rpm_build_dependencies:
        dependency = dependency.replace('python-', 'python3-')
        dependency = dependency.replace('python2-', 'python3-')
        rpm_build_dependencies.append(dependency)

    # TODO: check if already prefixed with python-

    python2_package_prefix = ''
    if project_definition.rpm_python2_prefix:
      python2_package_prefix = '{0:s}-'.format(
          project_definition.rpm_python2_prefix)

    elif project_definition.rpm_python2_prefix is None:
      python2_package_prefix = 'python2-'

    with io.open(output_file, 'w', encoding='utf8') as output_file_object:
      if project_definition.rpm_template_spec:
        result = self._WriteSpecFileFromTempate(
            project_definition.rpm_template_spec, project_version,
            output_file_object)
      else:
        result = self._RewriteSetupPyGeneratedFile(
            project_definition, source_directory, source_filename,
            project_name, rpm_build_dependencies, input_file,
            output_file_object, python2_package_prefix=python2_package_prefix)

    return result

  def RewriteSetupPyGeneratedFileForOSC(self, spec_file_path):
    """Rewrites the RPM spec file generated with setup.py for OSC.

    Args:
      spec_file_path (str): path of the RPM spec file.

    Returns:
      bool: True if successful, False otherwise.
    """
    with io.BytesIO() as temporary_file_object:
      with io.open(spec_file_path, 'r', encoding='utf8') as input_file_object:
        data = input_file_object.read()
        temporary_file_object.write(data)

      temporary_file_object.seek(0, os.SEEK_SET)

      with io.open(spec_file_path, 'w', encoding='utf8') as output_file_object:
        result = self._RewriteSetupPyGeneratedFileForOSC(
            temporary_file_object, output_file_object)

    return result
