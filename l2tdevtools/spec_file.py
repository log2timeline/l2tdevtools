# -*- coding: utf-8 -*-
"""RPM spec file generator."""

import datetime
import logging
import os
import subprocess
import sys


class RPMSpecFileGenerator(object):
  """Class that helps in generating RPM spec files."""

  _DOC_FILENAMES = [
      u'CHANGES', u'CHANGES.txt', u'CHANGES.TXT',
      u'README', u'README.txt', u'README.TXT']

  _LICENSE_FILENAMES = [
      u'LICENSE', u'LICENSE.txt', u'LICENSE.TXT']

  def GenerateWithSetupPy(self, source_directory, build_log_file):
    """Generates the RPM spec file with setup.py.

    Args:
      source_directory (str): path of the source directory.
      build_log_file (str): path of the build log file.

    Returns:
      bool: True if successful, False otherwise.
    """
    command = u'{0:s} setup.py bdist_rpm --spec-only >> {1:s} 2>&1'.format(
        sys.executable, build_log_file)
    exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def RewriteSetupPyGenerateFile(
      self, project_definition, source_directory, project_name, input_file,
      output_file):
    """Rewrites the RPM spec file generated with setup.py.

    Args:
      project_definition (ProjectDefinition): project definition.
      source_directory (str): path of the source directory.
      project_name (str): name of the project.
      input_file (str): path of the input RPM spec file.
      output_file (str): path of the output RPM spec file.

    Returns:
      bool: True if successful, False otherwise.
    """
    python2_only = project_definition.IsPython2Only()

    rpm_build_dependencies = [u'python2-setuptools']
    if project_definition.architecture_dependent:
      rpm_build_dependencies.append(u'python-devel')

    if not python2_only:
      rpm_build_dependencies.append(u'python3-setuptools')
      if project_definition.architecture_dependent:
        rpm_build_dependencies.append(u'python3-devel')

    if project_definition.rpm_build_dependencies:
      rpm_build_dependencies.extend(
          project_definition.rpm_build_dependencies)

    # TODO: check if already prefixed with python-

    output_file_object = open(output_file, 'wb')

    description = b''
    requires = b''
    summary = b''
    version = b''
    in_description = False
    has_build_requires = False
    has_python_package = False
    has_python3_package = False

    with open(input_file, 'r+b') as input_file_object:
      for line in input_file_object.readlines():
        if line.startswith(b'%') and in_description:
          in_description = False

          if project_definition.description_long:
            description = u'{0:s}\n\n'.format(
                project_definition.description_long)

          output_file_object.write(description)

        if line.startswith(b'%define name '):
          # Need to override the project name for projects that prefix
          # their name with "python-" in setup.py but do not use it
          # for their source package name.
          line = b'%define name {0:s}\n'.format(project_name)

        elif line.startswith(b'%define version '):
          version = line[16:-1]

        elif not summary and line.startswith(b'Summary: '):
          summary = line

        elif (not description and not requires and
              line.startswith(b'Requires: ')):
          requires = line
          continue

        elif line.startswith(b'BuildArch: noarch'):
          if project_definition.architecture_dependent:
            continue

        elif line.startswith(b'BuildRequires: '):
          has_build_requires = True
          line = b'BuildRequires: {0:s}\n'.format(b', '.join(
              rpm_build_dependencies))

        elif line == b'\n' and summary and not has_build_requires:
          has_build_requires = True
          line = b'BuildRequires: {0:s}\n'.format(b', '.join(
              rpm_build_dependencies))

        elif line.startswith(b'%description') and not description:
          in_description = True

        elif line.startswith(b'%package -n python-'):
          has_python_package = True

        elif line.startswith(b'%package -n python3-'):
          has_python3_package = True

        elif line.startswith(b'%prep'):
          if not has_python_package:
            python_requires = requires

            output_file_object.write((
                b'%package -n python-%{{name}}\n'
                b'{0:s}'
                b'{1:s}'
                b'\n'
                b'%description -n python-%{{name}}\n'
                b'{2:s}').format(summary, python_requires, description))

          if not python2_only and not has_python3_package:
            # TODO: convert python 2 package names to python 3
            python3_requires = requires

            output_file_object.write((
                b'%package -n python3-%{{name}}\n'
                b'{0:s}'
                b'{1:s}'
                b'\n'
                b'%description -n python3-%{{name}}\n'
                b'{2:s}').format(summary, python3_requires, description))

        elif line == b'%setup -n %{name}-%{unmangled_version}\n':
          line = b'%autosetup -n %{name}-%{unmangled_version}\n'

        elif line.startswith(b'python setup.py build'):
          if python2_only:
            line = b'python2 setup.py build\n'
          else:
            line = (
                b'python2 setup.py build\n'
                b'python3 setup.py build\n')

        elif line.startswith(b'python setup.py install'):
          if python2_only:
            line = (
                b'python2 setup.py install -O1 --root=%{buildroot}\n'
                b'rm -rf %{buildroot}/usr/share/doc/%{name}/\n')
          else:
            line = (
                b'python2 setup.py install -O1 --root=%{buildroot}\n'
                b'python3 setup.py install -O1 --root=%{buildroot}\n'
                b'rm -rf %{buildroot}/usr/share/doc/%{name}/\n')

        elif line == b'rm -rf $RPM_BUILD_ROOT\n':
          line = b'rm -rf %{buildroot}\n'

        elif line.startswith(b'%files'):
          break

        elif in_description:
          # Ignore leading white lines in the description.
          if not description and line == b'\n':
            continue

          description = b''.join([description, line])
          continue

        output_file_object.write(line)

    license_line = b''
    for license_file in self._LICENSE_FILENAMES:
      license_file_path = os.path.join(source_directory, license_file)
      if os.path.exists(license_file_path):
        license_line = b'%license {0:s}\n'.format(license_file)
        break

    doc_files = []
    for doc_file in self._DOC_FILENAMES:
      doc_file_path = os.path.join(source_directory, doc_file)
      if os.path.exists(doc_file_path):
        doc_files.append(doc_file)

    doc_line = b''
    if doc_files:
      doc_line = b'%doc {0:s}\n'.format(b' '.join(doc_files))

    if not project_definition.architecture_dependent:
      lib_dir = '%{_exec_prefix}/lib'
    else:
      lib_dir = '%{_libdir}'

    output_file_object.write((
        b'%files -n python-%{{name}}\n'
        b'{0:s}'
        b'{1:s}'
        b'{2:s}/python2*/*\n').format(
            license_line, doc_line, lib_dir))

    if not python2_only:
      output_file_object.write((
          b'\n'
          b'%files -n python3-%{{name}}\n'
          b'{0:s}'
          b'{1:s}'
          b'{2:s}/python3*/*\n').format(
              license_line, doc_line, lib_dir))

    # TODO: add bindir support.
    output_file_object.write((
        b'\n'
        b'%exclude %{_bindir}/*\n'))

    # TODO: add shared data support.

    date_time = datetime.datetime.now()
    date_time_string = date_time.strftime(u'%a %b %e %Y')

    output_file_object.write((
        b'\n'
        b'%changelog\n'
        b'* {0:s} Joachim Metz <joachim.metz@gmail.com> {1:s}-1\n'
        b'- Auto-generated\n').format(date_time_string, version))

    output_file_object.close()

    return True

  def RewriteSetupPyGenerateFileForOSC(
      self, project_definition, source_directory, project_name, input_file,
      output_file):
    """Rewrites the RPM spec file generated with setup.py for OSC.

    Args:
      project_definition (ProjectDefinition): project definition.
      source_directory (str): path of the source directory.
      project_name (str): name of the project.
      input_file (str): path of the input RPM spec file.
      output_file (str): path of the output RPM spec file.

    Returns:
      bool: True if successful, False otherwise.
    """
    python2_only = project_definition.IsPython2Only()

    osc_build_dependencies = [u'python-devel', u'python-setuptools']

    if not python2_only:
      osc_build_dependencies.append(u'python3-devel')
      osc_build_dependencies.append(u'python3-setuptools')

    if self._project_definition.osc_build_dependencies:
      osc_build_dependencies.extend(
          self._project_definition.osc_build_dependencies)

    # TODO: check if already prefixed with python-

    output_file_object = open(output_file, 'wb')

    description = b''
    requires = b''
    summary = b''
    version = b''
    in_description = False
    has_build_requires = False
    has_python_package = False
    has_python3_package = False

    with open(input_file, 'r+b') as input_file_object:
      for line in input_file_object.readlines():
        if line.startswith(b'%') and in_description:
          in_description = False

          if self._project_definition.description_long:
            description = u'{0:s}\n\n'.format(
                self._project_definition.description_long)

          output_file_object.write(description)

        if line.startswith(b'%define name '):
          # Need to override the project name for projects that prefix
          # their name with "python-" in setup.py but do not use it
          # for their source package name.
          line = b'%define name {0:s}\n'.format(project_name)

        elif line.startswith(b'%define version '):
          version = line[16:-1]

        elif not summary and line.startswith(b'Summary: '):
          summary = line

        elif (not description and not requires and
              line.startswith(b'Requires: ')):
          requires = line
          continue

        elif line.startswith(b'BuildArch: noarch'):
          if self._project_definition.architecture_dependent:
            continue

        elif line.startswith(b'BuildRequires: '):
          has_build_requires = True
          line = b'BuildRequires: {0:s}\n'.format(b', '.join(
              osc_build_dependencies))

        elif line == b'\n' and summary and not has_build_requires:
          has_build_requires = True
          line = b'BuildRequires: {0:s}\n'.format(b', '.join(
              osc_build_dependencies))

        elif line.startswith(b'%description') and not description:
          in_description = True

        elif line.startswith(b'%package -n python-'):
          has_python_package = True

        elif line.startswith(b'%package -n python3-'):
          has_python3_package = True

        elif line.startswith(b'%prep'):
          if not has_python_package:
            python_requires = requires

            output_file_object.write((
                b'%package -n python-%{{name}}\n'
                b'{0:s}'
                b'{1:s}'
                b'\n'
                b'%description -n python-%{{name}}\n'
                b'{2:s}').format(summary, python_requires, description))

          if not python2_only and not has_python3_package:
            # TODO: convert python 2 package names to python 3
            python3_requires = requires

            output_file_object.write((
                b'%package -n python3-%{{name}}\n'
                b'{0:s}'
                b'{1:s}'
                b'\n'
                b'%description -n python3-%{{name}}\n'
                b'{2:s}').format(summary, python3_requires, description))

        elif line == b'%setup -n %{name}-%{unmangled_version}\n':
          line = b'%autosetup -n %{name}-%{unmangled_version}\n'

        elif line.startswith(b'python setup.py build'):
          if python2_only:
            line = b'python2 setup.py build\n'
          else:
            line = (
                b'python2 setup.py build\n'
                b'python3 setup.py build\n')

        elif line.startswith(b'python setup.py install'):
          if python2_only:
            line = (
                b'python2 setup.py install -O1 --root=%{buildroot}\n'
                b'rm -rf %{buildroot}/usr/share/doc/%{name}/\n')
          else:
            line = (
                b'python2 setup.py install -O1 --root=%{buildroot}\n'
                b'python3 setup.py install -O1 --root=%{buildroot}\n'
                b'rm -rf %{buildroot}/usr/share/doc/%{name}/\n')

        elif line == b'rm -rf $RPM_BUILD_ROOT\n':
          line = b'rm -rf %{buildroot}\n'

        elif line.startswith(b'%files'):
          break

        elif in_description:
          # Ignore leading white lines in the description.
          if not description and line == b'\n':
            continue

          description = b''.join([description, line])
          continue

        output_file_object.write(line)

    license_line = b''
    for license_file in self._LICENSE_FILENAMES:
      license_file_path = os.path.join(source_directory, license_file)
      if os.path.exists(license_file_path):
        license_line = b'%license {0:s}\n'.format(license_file)
        break

    doc_files = []
    for doc_file in self._DOC_FILENAMES:
      doc_file_path = os.path.join(source_directory, doc_file)
      if os.path.exists(doc_file_path):
        doc_files.append(doc_file)

    doc_line = b''
    if doc_files:
      doc_line = b'%doc {0:s}\n'.format(b' '.join(doc_files))

    # Add _libdir support for arch dependent.

    output_file_object.write((
        b'%files -n python-%{{name}}\n'
        b'{0:s}'
        b'{1:s}'
        b'%{{_exec_prefix}}/lib/python2*/*\n').format(
            license_line, doc_line))

    if not python2_only:
      output_file_object.write((
          b'\n'
          b'%files -n python3-%{{name}}\n'
          b'{0:s}'
          b'{1:s}'
          b'%{{_exec_prefix}}/lib/python3*/*\n').format(
              license_line, doc_line))

    # TODO: add bindir support.
    output_file_object.write((
        b'\n'
        b'%exclude %{_bindir}/*\n'))

    # TODO: add shared data support.

    date_time = datetime.datetime.now()
    date_time_string = date_time.strftime(u'%a %b %e %Y')

    output_file_object.write((
        b'\n'
        b'%changelog\n'
        b'* {0:s} Joachim Metz <joachim.metz@gmail.com> {1:s}-1\n'
        b'- Auto-generated\n').format(date_time_string, version))

    output_file_object.close()

    return True
