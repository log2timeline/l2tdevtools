# -*- coding: utf-8 -*-
"""Helper for building projects from source."""

import glob
import logging
import os
import platform
import re
import shutil
import subprocess

from l2tdevtools.build_helpers import interface
from l2tdevtools import spec_file


class BaseRPMBuildHelper(interface.BuildHelper):
  """Helper to build RPM packages (.rpm)."""

  _BUILD_DEPENDENCIES = frozenset([
      'git',
      'binutils',
      'autoconf',
      'automake',
      'libtool',
      'gettext-devel',
      'make',
      'pkgconf',
      'gcc',
      'gcc-c++',
      'flex',
      'byacc',
      'rpm-build',
      'python3-dateutil',
      'python3-devel',
      'python3-setuptools',
      'python3-test',
  ])

  _BUILD_DEPENDENCY_PACKAGE_NAMES = {
      'bzip2': ['bzip2-devel'],
      'fuse': ['fuse-devel'],
      'libcrypto': ['openssl-devel'],
      'liblzma': ['xz-devel'],
      'pytest-runner': ['python3-pytest-runner'],
      'sqlite': ['sqlite-devel'],
      'zeromq': ['libzmq3-devel'],
      'zlib': ['zlib-devel']
  }

  def __init__(
      self, project_definition, l2tdevtools_path, dependency_definitions):
    """Initializes a build helper.

    Args:
      project_definition (ProjectDefinition): definition of the project
          to build.
      l2tdevtools_path (str): path to the l2tdevtools directory.
      dependency_definitions (dict[str, ProjectDefinition]): definitions of all
          projects, which is used to determine the properties of dependencies.
    """
    super(BaseRPMBuildHelper, self).__init__(
        project_definition, l2tdevtools_path, dependency_definitions)
    self.architecture = platform.machine()

    self.rpmbuild_path = os.path.join('~', 'rpmbuild')
    self.rpmbuild_path = os.path.expanduser(self.rpmbuild_path)

    self._rpmbuild_rpms_path = os.path.join(self.rpmbuild_path, 'RPMS')
    self._rpmbuild_sources_path = os.path.join(self.rpmbuild_path, 'SOURCES')
    self._rpmbuild_specs_path = os.path.join(self.rpmbuild_path, 'SPECS')
    self._rpmbuild_srpms_path = os.path.join(self.rpmbuild_path, 'SRPMS')

  def _BuildFromSpecFile(self, spec_filename, rpmbuild_flags='-ba'):
    """Builds the rpms directly from a spec file.

    Args:
      spec_filename (str): name of the spec file as stored in the rpmbuild
          SPECS sub directory.
      rpmbuild_flags (Optional(str)): rpmbuild flags.

    Returns:
      bool: True if successful, False otherwise.
    """
    spec_filename = os.path.join('SPECS', spec_filename)

    current_path = os.getcwd()
    os.chdir(self.rpmbuild_path)

    command = 'rpmbuild {0:s} {1:s} > {2:s} 2>&1'.format(
        rpmbuild_flags, spec_filename, self.LOG_FILENAME)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))

    os.chdir(current_path)

    return exit_code == 0

  def _BuildFromSourcePackage(
      self, source_package_filename, rpmbuild_flags='-ta'):
    """Builds the rpms directly from the source package file.

    For this to work the source package needs to contain a valid rpm .spec file.

    Args:
      source_package_filename (str): name of the source package file.
      rpmbuild_flags (Optional(str)): rpmbuild flags.

    Returns:
      bool: True if successful, False otherwise.
    """
    command = 'rpmbuild {0:s} {1:s} > {2:s} 2>&1'.format(
        rpmbuild_flags, source_package_filename, self.LOG_FILENAME)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _CheckIsInstalled(self, package_name):
    """Checks if a package is installed.

    Args:
      package_name (str): name of the package.

    Returns:
      bool: True if the package is installed, False otherwise.
    """
    command = 'rpm -qi {0:s} >/dev/null 2>&1'.format(package_name)
    exit_code = subprocess.call(command, shell=True)
    return exit_code == 0

  def _CopySourcePackageToRPMBuildSources(self, source_package_path):
    """Copies the source package to the rpmbuild SOURCES directory.

    Args:
      source_package_path (str): path of the source package file.
    """
    source_package_filename = os.path.basename(source_package_path)
    rpm_source_package_path = os.path.join(
        self._rpmbuild_sources_path, source_package_filename)

    if not os.path.exists(rpm_source_package_path):
      self._CreateRPMbuildDirectories()

      shutil.copy(source_package_path, rpm_source_package_path)

  def _CreateRPMbuildDirectories(self):
    """Creates the rpmbuild and sub directories."""
    if not os.path.exists(self.rpmbuild_path):
      os.mkdir(self.rpmbuild_path)

    if not os.path.exists(self._rpmbuild_sources_path):
      os.mkdir(self._rpmbuild_sources_path)

    if not os.path.exists(self._rpmbuild_specs_path):
      os.mkdir(self._rpmbuild_specs_path)

  def _CreateSpecFile(self, project_name, spec_file_data):
    """Creates a spec file in the rpmbuild directory.

    Args:
      project_name (str): name of the project.
      spec_file_data (str): spec file data.
    """
    spec_filename = os.path.join(
        self._rpmbuild_specs_path, '{0:s}.spec'.format(project_name))

    with open(spec_filename, 'w', encoding='utf-8') as rpm_spec_file:
      rpm_spec_file.write(spec_file_data)

  def _CopySourceFile(self, source_package_path):
    """Copies the source file to the rpmbuild directory.

    Args:
      source_package_path (str): path of the source package file.
    """
    shutil.copy(source_package_path, self._rpmbuild_sources_path)

  def _GetFilenameSafeProjectInformation(self, source_helper_object):
    """Determines the filename safe project name and version.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      tuple: containing:

        * str: filename safe project name.
        * str: version.
    """
    project_name = source_helper_object.project_name

    project_version = source_helper_object.GetProjectVersion()
    if project_version and project_version.startswith('1!'):
      # Remove setuptools epoch.
      project_version = project_version[2:]

    return project_name, project_version

  def _MoveFilesToCurrentDirectory(self, filenames_glob):
    """Moves files into the current directory.

    Args:
      filenames_glob (str): glob of the filenames to move.
    """
    filenames = glob.glob(filenames_glob)
    for filename in filenames:
      logging.info('Moving: {0:s}'.format(filename))

      local_filename = os.path.basename(filename)
      if os.path.exists(local_filename):
        os.remove(local_filename)

      shutil.move(filename, '.')

  def CheckBuildDependencies(self):
    """Checks if the build dependencies are met.

    Returns:
      list[str]: build dependency names that are not met or an empty list.
    """
    missing_packages = []
    for package_name in self._BUILD_DEPENDENCIES:
      if not self._CheckIsInstalled(package_name):
        missing_packages.append(package_name)

    for package_name in self._project_definition.build_dependencies:
      dependencies = self._BUILD_DEPENDENCY_PACKAGE_NAMES.get(
          package_name, [package_name])
      for dependency in dependencies:
        if not self._CheckIsInstalled(dependency):
          missing_packages.append(dependency)

    return missing_packages


class RPMBuildHelper(BaseRPMBuildHelper):
  """Helper to build RPM packages (.rpm)."""

  def _RemoveBuildDirectory(self, project_name, project_version):
    """Removes build directory.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
    """
    filename = '{0:s}-{1!s}'.format(project_name, project_version)
    filename = os.path.join(self.rpmbuild_path, 'BUILD', filename)

    if os.path.exists(filename):
      logging.info('Removing: {0:s}'.format(filename))
      try:
        shutil.rmtree(filename)
      except OSError:
        logging.warning('Unable to remove: {0:s}'.format(filename))

  def _RemoveOlderBuildDirectory(self, project_name, project_version):
    """Removes previous versions of build directories.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
    """
    filenames_to_ignore = '{0:s}-{1!s}'.format(
        project_name, project_version)
    filenames_to_ignore = re.compile(filenames_to_ignore)

    filenames_glob = os.path.join(
        self.rpmbuild_path, 'BUILD', '{0:s}-*'.format(project_name))
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        shutil.rmtree(filename, ignore_errors=True)

  def _RemoveOlderRPMs(self, project_name, project_version):
    """Removes previous versions of .rpm files.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
    """
    filenames_to_ignore = '.*{0:s}-.*{1!s}-1.{2:s}.rpm'.format(
        project_name, project_version, self.architecture)
    filenames_to_ignore = re.compile(filenames_to_ignore)

    rpm_filenames_glob = '*{0:s}-*-1.{1:s}.rpm'.format(
        project_name, self.architecture)
    filenames = glob.glob(rpm_filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_glob = os.path.join(
        self.rpmbuild_path, 'RPMS', self.architecture, rpm_filenames_glob)
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if a build is required, False otherwise.
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    rpm_filename = '{0:s}-{1!s}-1.{2:s}.rpm'.format(
        project_name, project_version, self.architecture)

    return not os.path.exists(rpm_filename)


class ConfigureMakeRPMBuildHelper(RPMBuildHelper):
  """Helper to build RPM packages (.rpm)."""

  def _MoveRPMs(self, project_name, project_version):
    """Moves the rpms from the rpmbuild directory into the current directory.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
    """
    rpm_name = self._project_definition.rpm_name or project_name

    filenames_glob = '{0:s}-*{1!s}-1.{2:s}.rpm'.format(
        rpm_name, project_version, self.architecture)
    filenames_glob = os.path.join(
        self._rpmbuild_rpms_path, self.architecture, filenames_glob)

    self._MoveFilesToCurrentDirectory(filenames_glob)

  def Build(self, source_helper_object):
    """Builds the rpms.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_package_path = source_helper_object.GetSourcePackagePath()
    if not source_package_path:
      logging.info('Missing source package of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    source_package_filename = source_helper_object.GetSourcePackageFilename()
    logging.info('Building rpm of: {0:s}'.format(source_package_filename))

    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    # rpmbuild wants the source package filename without the status indication.
    rpm_source_package_filename = '{0:s}-{1!s}.tar.gz'.format(
        project_name, project_version)
    if not os.path.exists(rpm_source_package_filename):
      shutil.copyfile(source_package_path, rpm_source_package_filename)

    build_successful = self._BuildFromSourcePackage(
        rpm_source_package_filename, rpmbuild_flags='-tb')

    if build_successful:
      self._MoveRPMs(project_name, project_version)

      setup_name = self._project_definition.setup_name or project_name
      self._RemoveBuildDirectory(setup_name, project_version)

    return build_successful

  def Clean(self, source_helper_object):
    """Cleans the rpmbuild directory.

    Args:
      source_helper_object (SourceHelper): source helper.
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    self._RemoveOlderSourceDirectories(project_name, project_version)
    self._RemoveOlderSourcePackages(project_name, project_version)

    setup_name = self._project_definition.setup_name or project_name
    self._RemoveOlderBuildDirectory(setup_name, project_version)

    self._RemoveOlderRPMs(project_name, project_version)


class PyprojectRPMBuildHelper(RPMBuildHelper):
  """Helper to build RPM packages (.rpm)."""

  def __init__(
      self, project_definition, l2tdevtools_path, dependency_definitions):
    """Initializes a build helper.

    Args:
      project_definition (ProjectDefinition): definition of the project
          to build.
      l2tdevtools_path (str): path to the l2tdevtools directory.
      dependency_definitions (dict[str, ProjectDefinition]): definitions of all
          projects, which is used to determine the properties of dependencies.
    """
    super(PyprojectRPMBuildHelper, self).__init__(
        project_definition, l2tdevtools_path, dependency_definitions)
    if not project_definition.architecture_dependent:
      self.architecture = 'noarch'

  def _GenerateSpecFile(
      self, project_name, project_version, source_package_filename,
      source_helper_object):
    """Generates the rpm spec file.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
      source_package_filename (str): name of the source package file.
      source_helper_object (SourceHelper): source helper.

    Returns:
      str: path of the generated rpm spec file or None if not available.
    """
    source_directory = source_helper_object.GetSourceDirectoryPath()
    if not source_directory:
      logging.info('Missing source directory of: {0:s}'.format(
          source_helper_object.project_name))
      return None

    spec_file_generator = spec_file.RPMSpecFileGenerator(self._data_path)

    if project_name.startswith('python-'):
      project_name = project_name[7:]

    spec_filename = '{0:s}.spec'.format(project_name)
    output_file_path = os.path.join(self._rpmbuild_specs_path, spec_filename)

    try:
      result = spec_file_generator.Generate(
          self._project_definition, source_directory, source_package_filename,
          project_name, project_version, output_file_path)
    except (FileNotFoundError, TypeError):
      result = False

    if not result:
      return None

    return output_file_path

  def _MoveRPMs(self, project_name, project_version):
    """Moves the rpms from the rpmbuild directory into the current directory.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
    """
    rpm_name = self._project_definition.rpm_name or project_name
    if (rpm_name.startswith('python-') or rpm_name.startswith('python2-') or
        rpm_name.startswith('python3-')):
      _, _, rpm_name = rpm_name.partition('-')

    # TODO: add support for rpm_python_prefix.
    filenames_glob = 'python*-{0:s}-*{1!s}-1.{2:s}.rpm'.format(
        rpm_name, project_version, self.architecture)
    filenames_glob = os.path.join(
        self._rpmbuild_rpms_path, self.architecture, filenames_glob)

    self._MoveFilesToCurrentDirectory(filenames_glob)

    filenames_glob = '{0:s}-*{1!s}-1.{2:s}.rpm'.format(
        rpm_name, project_version, self.architecture)
    filenames_glob = os.path.join(
        self._rpmbuild_rpms_path, self.architecture, filenames_glob)

    self._MoveFilesToCurrentDirectory(filenames_glob)

  def Build(self, source_helper_object):
    """Builds the rpms.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_package_path = source_helper_object.GetSourcePackagePath()
    if not source_package_path:
      logging.info('Missing source package of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    source_package_filename = source_helper_object.GetSourcePackageFilename()
    logging.info('Building rpm of: {0:s}'.format(source_package_filename))

    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    self._CopySourcePackageToRPMBuildSources(source_package_path)

    rpm_spec_file_path = self._GenerateSpecFile(
        project_name, project_version, source_package_filename,
        source_helper_object)
    if not rpm_spec_file_path:
      logging.error('Unable to generate rpm spec file.')
      return False

    build_successful = self._BuildFromSpecFile(
        rpm_spec_file_path, rpmbuild_flags='-bb')

    if build_successful:
      self._MoveRPMs(project_name, project_version)

      setup_name = self._project_definition.setup_name or project_name
      self._RemoveBuildDirectory(setup_name, project_version)

    return build_successful

  def Clean(self, source_helper_object):
    """Cleans the build and dist directory.

    Args:
      source_helper_object (SourceHelper): source helper.
    """
    # Remove previous versions build directories.
    for filename in ('build', 'dist'):
      if os.path.exists(filename):
        logging.info('Removing: {0:s}'.format(filename))
        shutil.rmtree(filename, ignore_errors=True)

    # Remove previous versions of rpms.
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    # The setup.py directory name can differ from the project name.
    setup_name = self._project_definition.setup_name or project_name

    self._RemoveOlderSourceDirectories(setup_name, project_version)
    self._RemoveOlderSourcePackages(project_name, project_version)

    self._RemoveOlderBuildDirectory(setup_name, project_version)

    self._RemoveOlderRPMs(project_name, project_version)


class SRPMBuildHelper(BaseRPMBuildHelper):
  """Helper to build source RPM packages (.src.rpm)."""

  def _MoveRPMs(self, project_name, project_version):
    """Moves the rpms from the rpmbuild directory into the current directory.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
    """
    srpm_name = self._project_definition.srpm_name or project_name
    if (srpm_name.startswith('python-') or srpm_name.startswith('python2-') or
        srpm_name.startswith('python3-')):
      _, _, srpm_name = srpm_name.partition('-')

    filenames_glob = '{0:s}-*{1!s}-1.src.rpm'.format(srpm_name, project_version)
    filenames_glob = os.path.join(self._rpmbuild_srpms_path, filenames_glob)

    self._MoveFilesToCurrentDirectory(filenames_glob)

  def _RemoveOlderSourceRPMs(self, project_name, project_version):
    """Removes previous versions of .src.rpm files.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
    """
    filenames_to_ignore = '{0:s}-.*{1!s}-1.src.rpm'.format(
        project_name, project_version)
    filenames_to_ignore = re.compile(filenames_to_ignore)

    src_rpm_filenames_glob = '{0:s}-*-1.src.rpm'.format(project_name)
    filenames = glob.glob(src_rpm_filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_glob = os.path.join(
        self.rpmbuild_path, 'SRPMS', src_rpm_filenames_glob)
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if a build is required, False otherwise.
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    srpm_filename = '{0:s}-{1!s}-1.src.rpm'.format(
        project_name, project_version)

    return not os.path.exists(srpm_filename)

  def Clean(self, source_helper_object):
    """Cleans the rpmbuild directory.

    Args:
      source_helper_object (SourceHelper): source helper.
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    self._RemoveOlderSourceDirectories(project_name, project_version)
    self._RemoveOlderSourcePackages(project_name, project_version)

    self._RemoveOlderSourceRPMs(project_name, project_version)


class ConfigureMakeSRPMBuildHelper(SRPMBuildHelper):
  """Helper to build source RPM packages (.src.rpm)."""

  def Build(self, source_helper_object):
    """Builds the source rpm.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_package_path = source_helper_object.GetSourcePackagePath()
    if not source_package_path:
      logging.info('Missing source package of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    source_package_filename = source_helper_object.GetSourcePackageFilename()
    logging.info('Building source rpm of: {0:s}'.format(
        source_package_filename))

    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    # rpmbuild wants the source package filename without the status indication.
    rpm_source_package_filename = '{0:s}-{1!s}.tar.gz'.format(
        project_name, project_version)
    shutil.copyfile(source_package_path, rpm_source_package_filename)

    build_successful = self._BuildFromSourcePackage(
        rpm_source_package_filename, rpmbuild_flags='-ts')

    # TODO: test binary build of source package?

    if build_successful:
      self._MoveRPMs(project_name, project_version)

    return build_successful


class PyprojectSRPMBuildHelper(SRPMBuildHelper):
  """Helper to build source RPM packages (.src.rpm)."""

  def __init__(
      self, project_definition, l2tdevtools_path, dependency_definitions):
    """Initializes a build helper.

    Args:
      project_definition (ProjectDefinition): definition of the project
          to build.
      l2tdevtools_path (str): path to the l2tdevtools directory.
      dependency_definitions (dict[str, ProjectDefinition]): definitions of all
          projects, which is used to determine the properties of dependencies.
    """
    super(PyprojectSRPMBuildHelper, self).__init__(
        project_definition, l2tdevtools_path, dependency_definitions)
    if not project_definition.architecture_dependent:
      self.architecture = 'noarch'

  def _GenerateSpecFile(
      self, project_name, project_version, source_package_filename,
      source_helper_object):
    """Generates the rpm spec file.

    Args:
      project_name (str): name of the project.
      project_version (str): version of the project.
      source_package_filename (str): name of the source package file.
      source_helper_object (SourceHelper): source helper.

    Returns:
      str: path of the generated rpm spec file or None if not available.
    """
    source_directory = source_helper_object.GetSourceDirectoryPath()
    if not source_directory:
      logging.info('Missing source directory of: {0:s}'.format(
          source_helper_object.project_name))
      return None

    spec_file_generator = spec_file.RPMSpecFileGenerator(self._data_path)

    if project_name.startswith('python-'):
      project_name = project_name[7:]

    spec_filename = '{0:s}.spec'.format(project_name)
    output_file_path = os.path.join(self._rpmbuild_specs_path, spec_filename)

    try:
      result = spec_file_generator.Generate(
          self._project_definition, source_directory, source_package_filename,
          project_name, project_version, output_file_path)
    except (FileNotFoundError, TypeError):
      result = False

    if not result:
      return None

    return output_file_path

  def Build(self, source_helper_object):
    """Builds the source rpm.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_package_path = source_helper_object.GetSourcePackagePath()
    if not source_package_path:
      logging.info('Missing source package of: {0:s}'.format(
          source_helper_object.project_name))
      return False

    source_package_filename = source_helper_object.GetSourcePackageFilename()
    logging.info('Building source rpm of: {0:s}'.format(
        source_package_filename))

    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    self._CopySourcePackageToRPMBuildSources(source_package_path)

    rpm_spec_file_path = self._GenerateSpecFile(
        project_name, project_version, source_package_filename,
        source_helper_object)
    if not rpm_spec_file_path:
      logging.error('Unable to generate rpm spec file.')
      return False

    build_successful = self._BuildFromSpecFile(
        rpm_spec_file_path, rpmbuild_flags='-bs')

    # TODO: test binary build of source package?

    if build_successful:
      self._MoveRPMs(project_name, project_version)

    return build_successful
