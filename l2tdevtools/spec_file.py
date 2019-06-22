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

  def _GetBuildDefinition(self, python2_only):
    """Retrieves the build definition.

    Args:
      python2_only (bool): True if the spec file should build Python 2
          packages only.

    Returns:
      str: build definition.
    """
    lines = [b'%py2_build']
    if not python2_only:
      lines.append(b'%py3_build')

    lines.append(b'')
    return b'\n'.join(lines)

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

    doc_file_definition = b''
    if doc_files:
      doc_file_definition = b'%doc {0:s}\n'.format(b' '.join(doc_files))

    return doc_file_definition

  def _GetInstallDefinition(self, project_name, python2_only):
    """Retrieves the install definition.

    Args:
      project_name (str): name of the project.
      python2_only (bool): True if the spec file should build Python 2
          packages only.

    Returns:
      str: install definition.
    """
    lines = [b'%py2_install']
    if not python2_only:
      lines.append(b'%py3_install')

    lines.extend([
        b'rm -rf %{buildroot}/usr/share/doc/%{name}/'])

    if project_name == 'astroid':
      lines.append('rm -rf %{buildroot}%{python2_sitelib}/astroid/tests')
      if not python2_only:
        lines.append('rm -rf %{buildroot}%{python3_sitelib}/astroid/tests')

    elif project_name == 'pylint':
      lines.append('rm -rf %{buildroot}%{python2_sitelib}/pylint/test')
      if not python2_only:
        lines.append('rm -rf %{buildroot}%{python3_sitelib}/pylint/test')

    lines.append(b'')
    return b'\n'.join(lines)

  def _GetLicenseFileDefinition(self, source_directory):
    """Retrieves the license file definition.

    Args:
      source_directory (str): path of the source directory.

    Returns:
      str: license file definition.
    """
    license_file_definition = b''
    for license_file in self._LICENSE_FILENAMES:
      license_file_path = os.path.join(source_directory, license_file)
      if os.path.exists(license_file_path):
        license_file_definition = b'%license {0:s}\n'.format(license_file)
        break

    return license_file_definition

  def _WriteChangeLog(self, output_file_object, version):
    """Writes the change log.

    Args:
      output_file_object (file): output file-like object to write to.
      version (str): version.
    """
    date_time = datetime.datetime.now()
    date_time_string = date_time.strftime('%a %b %e %Y')

    output_file_object.write((
        b'\n'
        b'%changelog\n'
        b'* {0:s} {1:s} {2:s}-1\n'
        b'- Auto-generated\n').format(
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
    output_file_object.write(b'%package -n {0:s}\n'.format(name))
    if name == 'pytz':
      output_file_object.write(
          b'Obsoletes: %{name} < %{version}\n'
          b'Provides: %{name} = %{version}\n')
    else:
      output_file_object.write(
          b'Obsoletes: python-%{name} < %{version}\n'
          b'Provides: python-%{name} = %{version}\n')

    if requires:
      output_file_object.write(b'Requires: {0:s}\n'.format(', '.join(requires)))

    output_file_object.write((
        b'{0:s}'
        b'\n'
        b'%description -n {1:s}\n'
        b'{2:s}').format(summary, name, description))

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
          b'%files -n {0:s}\n'
          b'{1:s}'
          b'{2:s}'
          b'%{{python2_sitelib}}/\n').format(
              name, license_line, doc_line))

    elif project_name == 'pytsk3':
      output_file_object.write((
          b'%files -n {0:s}\n'
          b'{1:s}'
          b'{2:s}'
          b'%{{_libdir}}/python2*/site-packages/{3:s}*.so\n'
          b'%{{_libdir}}/python2*/site-packages/{3:s}*.egg-info\n').format(
              name, license_line, doc_line, setup_name))

    elif project_definition.architecture_dependent:
      output_file_object.write((
          b'%files -n {0:s}\n'
          b'{1:s}'
          b'{2:s}'
          b'%{{_libdir}}/python2*/site-packages/{3:s}\n'
          b'%{{_libdir}}/python2*/site-packages/{3:s}*.egg-info\n').format(
              name, license_line, doc_line, setup_name))

    else:
      output_file_object.write((
          b'%files -n {0:s}\n'
          b'{1:s}'
          b'{2:s}'
          b'%{{python2_sitelib}}/{3:s}\n'
          b'%{{python2_sitelib}}/{3:s}*.egg-info\n').format(
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
    output_file_object.write(b'%package -n {0:s}\n'.format(name))

    if requires:
      output_file_object.write(b'Requires: {0:s}\n'.format(', '.join(requires)))

    output_file_object.write((
        b'{0:s}'
        b'\n'
        b'%description -n {1:s}\n'
        b'{2:s}').format(summary, name, description))

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
          b'\n'
          b'%files -n {0:s}\n'
          b'{1:s}'
          b'{2:s}'
          b'%{{python3_sitelib}}/\n').format(
              name, license_line, doc_line))

    elif project_name == 'pytsk3':
      output_file_object.write((
          b'\n'
          b'%files -n {0:s}\n'
          b'{1:s}'
          b'{2:s}'
          b'%{{_libdir}}/python3*/site-packages/{3:s}*.so\n'
          b'%{{_libdir}}/python3*/site-packages/{3:s}*.egg-info\n').format(
              name, license_line, doc_line, setup_name))

    elif project_definition.architecture_dependent:
      output_file_object.write((
          b'\n'
          b'%files -n {0:s}\n'
          b'{1:s}'
          b'{2:s}'
          b'%{{_libdir}}/python3*/site-packages/{3:s}\n'
          b'%{{_libdir}}/python3*/site-packages/{3:s}*.egg-info\n').format(
              name, license_line, doc_line, setup_name))

    else:
      output_file_object.write((
          b'\n'
          b'%files -n {0:s}\n'
          b'{1:s}'
          b'{2:s}'
          b'%{{python3_sitelib}}/{3:s}\n'
          b'%{{python3_sitelib}}/{3:s}*.egg-info\n').format(
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
    description = b''
    requires = b''
    summary = b''
    version = b''
    python_requires = b''

    in_description = False
    in_python_package = False
    has_build_requires = False
    has_python2_package = False
    has_python3_package = False
    has_unmangled_version = False

    python2_only = project_definition.IsPython2Only()

    if project_definition.rpm_name:
      package_name = project_definition.rpm_name
    else:
      package_name = project_name

    if package_name.startswith('python-'):
      package_name = package_name[7:]

    unmangled_name = project_name

    with open(input_file, 'r+b') as input_file_object:
      for line in input_file_object.readlines():
        if line.startswith(b'%') and in_description:
          in_description = False

          if project_definition.description_long:
            description = b'{0:s}\n\n'.format(
                project_definition.description_long)

          output_file_object.write(description)

        if line.startswith(b'%prep') and in_python_package:
          in_python_package = False

        if in_python_package and project_name == 'plaso':
          continue

        if line.startswith(b'%define name '):
          # Need to override the project name for projects that prefix
          # their name with "python-" (or equivalent) in setup.py but
          # do not use it for their source package name.
          line = b'%define name {0:s}\n'.format(project_name)

        elif line.startswith(b'%define version '):
          version = line[16:-1]
          if version.startswith(b'1!'):
            version = version[2:]

        elif line.startswith(b'%define unmangled_version '):
          # setup.py generates %define unmangled_version twice ignore
          # the second define.
          if has_unmangled_version:
            continue

          output_file_object.write(
              b'%define unmangled_name {0:s}\n'.format(unmangled_name))

          has_unmangled_version = True

        elif not summary and line.startswith(b'Summary: '):
          summary = line

        elif line.startswith(b'Source0: '):
          if source_filename.endswith('.zip'):
            line = b'Source0: %{unmangled_name}-%{unmangled_version}.zip\n'
          else:
            line = b'Source0: %{unmangled_name}-%{unmangled_version}.tar.gz\n'

        elif line.startswith(b'BuildRoot: '):
          if project_name == 'psutil':
            line = (
                b'BuildRoot: %{_tmppath}/'
                b'%{name}-release-%{version}-%{release}-buildroot\n')

          else:
            line = (
                b'BuildRoot: %{_tmppath}/'
                b'%{unmangled_name}-release-%{version}-%{release}-buildroot\n')

        elif (not description and not requires and
              line.startswith(b'Requires: ')):
          requires = line
          continue

        elif (in_python_package and not python_requires and
              line.startswith(b'Requires: ')):
          python2_requires = self._SplitRequires(line)
          if python2_requires:
            line = b'Requires: {0:s}\n'.format(
                ', '.join(python2_requires))

          python_requires = line

        elif line.startswith(b'BuildArch: noarch'):
          if project_definition.architecture_dependent:
            continue

        elif line.startswith(b'BuildRequires: '):
          has_build_requires = True
          line = b'BuildRequires: {0:s}\n'.format(b', '.join(
              rpm_build_dependencies))

        elif line == b'\n' and summary and not has_build_requires:
          has_build_requires = True
          line = b'BuildRequires: {0:s}\n\n'.format(b', '.join(
              rpm_build_dependencies))

        elif line.startswith(b'%description') and not description:
          in_description = True

        elif (line.startswith(b'%package -n python-') or
              line.startswith(b'%package -n python2-')):
          in_python_package = True
          has_python2_package = True

          if line.startswith(b'%package -n python2-'):
            if python2_package_prefix == 'python-':
              logging.warning(
                  'rpm_python_package prefix is: "python" but spec file '
                  'defines: "python2"')
            python2_package_prefix = 'python2-'

        elif line.startswith(b'%package -n python3-'):
          has_python3_package = True

        elif line.startswith(b'%prep'):
          if project_name == 'plaso':
            requires = b'{0:s}, {1:s}-data\n'.format(
                requires[:-1], project_name)

          if not has_python2_package:
            if project_name != package_name:
              python_package_name = b'{0:s}{1:s}'.format(
                  python2_package_prefix, package_name)
            else:
              python_package_name = b'{0:s}%{{name}}'.format(
                  python2_package_prefix)

            if python_package_name != b'%{name}':
              python2_requires = self._SplitRequires(requires)
              self._WritePython2PackageDefinition(
                  output_file_object, python_package_name, summary,
                  python2_requires, description)

          if not python2_only and not has_python3_package:
            if project_name != package_name:
              python_package_name = b'python3-{0:s}'.format(package_name)
            else:
              python_package_name = b'python3-%{name}'

            python3_requires = python_requires
            if not python3_requires:
              python3_requires = requires

            python3_requires = python3_requires.replace(
                '-python2 ', '-python3 ')
            python3_requires = python3_requires.replace('-python ', '-python3 ')
            python3_requires = python3_requires.replace(
                ' python2-', ' python3-')
            python3_requires = python3_requires.replace(' python-', ' python3-')

            # Remove Python 2 only dependencies like backports or pysqlite.
            python3_requires = [
                require for require in self._SplitRequires(python3_requires)
                if 'backports' not in require and 'pysqlite' not in require]

            self._WritePython3PackageDefinition(
                output_file_object, python_package_name, summary,
                python3_requires, description)

          if project_name == 'plaso':
            output_file_object.write((
                b'%package -n %{{name}}-data\n'
                b'{0:s}'
                b'\n'
                b'%description -n %{{name}}-data\n'
                b'{1:s}').format(summary, description))

        elif line.startswith(b'%setup -n %{name}-%{unmangled_version}'):
          if project_name == 'psutil':
            line = b'%autosetup -n %{name}-release-%{unmangled_version}\n'
          else:
            line = b'%autosetup -n %{unmangled_name}-%{unmangled_version}\n'

        elif (line.startswith(b'python setup.py build') or
              line.startswith(b'python2 setup.py build') or
              line.startswith(b'%py2_build') or line.startswith(
                  b'env CFLAGS="$RPM_OPT_FLAGS" python setup.py build')):
          line = self._GetBuildDefinition(python2_only)

        elif (line.startswith(b'python setup.py install') or
              line.startswith(b'python2 setup.py install') or
              line.startswith(b'%py2_install')):
          line = self._GetInstallDefinition(project_name, python2_only)

        elif line == b'rm -rf $RPM_BUILD_ROOT\n':
          line = b'rm -rf %{buildroot}\n'

        elif (line.startswith(b'%files') and
              not line.startswith(b'%files -n %{name}-data')):
          break

        elif in_description:
          # Ignore leading white lines in the description.
          if not description and line == b'\n':
            continue

          description = b''.join([description, line])
          continue

        output_file_object.write(line)

    license_line = self._GetLicenseFileDefinition(source_directory)

    doc_line = self._GetDocumentationFilesDefinition(source_directory)

    if project_name != package_name:
      python_package_name = b'{0:s}{1:s}'.format(
          python2_package_prefix, package_name)
    else:
      python_package_name = b'{0:s}%{{name}}'.format(python2_package_prefix)

    self._WritePython2PackageFiles(
        output_file_object, project_definition, project_name,
        python_package_name, license_line, doc_line)

    if not python2_only:
      if project_name != package_name:
        python_package_name = b'python3-{0:s}'.format(package_name)
      else:
        python_package_name = b'python3-%{name}'

      self._WritePython3PackageFiles(
          output_file_object, project_definition, project_name,
          python_package_name, license_line, doc_line)

    if project_name == 'plaso':
      output_file_object.write(
          b'\n'
          b'%files -n %{name}-data\n'
          b'%{_datadir}/%{name}/*\n')

    # TODO: add bindir support.
    output_file_object.write((
        b'\n'
        b'%exclude %{_bindir}/*\n'))

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

        if line.startswith(b'%exclude %{python3_sitelib}'):
          output_file_object.write(line)
          continue

        output_file_object.write(b'%endif # %{defined fedora} >= 28\n')
        output_file_object.write(b'\n')

        in_python3_package = False

      elif (not in_python3_package and line.startswith(b'BuildRequires: ') and
            b'python' in line):
        build_requires = [require.strip() for require in line[15:].split(',')]
        python_build_requires = [
            require.strip() for require in build_requires
            if 'python3' not in require]

        output_file_object.write(b'%if %{defined fedora} >= 28\n')
        output_file_object.write(b'BuildRequires: {0:s}\n'.format(', '.join(
            build_requires)))
        output_file_object.write(b'%else\n')
        output_file_object.write(b'BuildRequires: {0:s}\n'.format(', '.join(
            python_build_requires)))
        output_file_object.write(b'%endif\n')
        continue

      elif line.startswith(b'%files -n python3-') or (
          line.startswith(b'%files -n ') and line.endswith(b'-python3\n')):
        output_file_object.write(b'%if %{defined fedora} >= 28\n')
        output_file_object.write(b'\n')

        in_python3_package = True

      elif line.startswith(b'%package -n python3-') or (
          line.startswith(b'%package -n ') and line.endswith(b'-python3\n')):
        output_file_object.write(b'%if %{defined fedora} >= 28\n')
        output_file_object.write(b'\n')

        in_python3_package = True

      elif line.startswith(b'%py3_build') or line.startswith(b'%py3_install'):
        output_file_object.write(b'%if %{defined fedora} >= 28\n')
        output_file_object.write(line)
        output_file_object.write(b'%endif\n')
        continue

      elif (line.startswith(b'%configure ') and
            b'--enable-python2 --enable-python3' in line):
        output_file_object.write(b'%if %{defined fedora} >= 28\n')
        output_file_object.write(line)
        output_file_object.write(b'%else\n')
        line = line.replace(
            '--enable-python2 --enable-python3', '--enable-python')
        output_file_object.write(line)
        output_file_object.write(b'%endif\n')
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
    with open(template_file_path, 'rb') as file_object:
      rules_template = file_object.read()

    rules_template = rules_template.decode('utf-8')

    data = rules_template.format(**template_values)
    data = data.encode('utf-8')

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
    python2_only = project_definition.IsPython2Only()

    if project_name in ('guppy', 'lz4', 'psutil', 'pysqlite', 'yara-python'):
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

    if not python2_only:
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

    with open(output_file, 'wb') as output_file_object:
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
      with open(spec_file_path, 'rb') as input_file_object:
        data = input_file_object.read()
        temporary_file_object.write(data)

      temporary_file_object.seek(0, os.SEEK_SET)

      with open(spec_file_path, 'wb') as output_file_object:
        result = self._RewriteSetupPyGeneratedFileForOSC(
            temporary_file_object, output_file_object)

    return result
