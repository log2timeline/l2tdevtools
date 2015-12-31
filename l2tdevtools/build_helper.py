# -*- coding: utf-8 -*-
"""Build helper object implementations."""

from __future__ import print_function
import fileinput
import glob
import logging
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys

from l2tdevtools import dpkg_files
from l2tdevtools import download_helper
from l2tdevtools import source_helper


class BuildHelper(object):
  """Base class that helps in building."""

  LOG_FILENAME = u'build.log'

  def __init__(self, dependency_definition, l2tdevtools_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      l2tdevtools_path: the path to the l2tdevtools directory.
    """
    super(BuildHelper, self).__init__()
    self._data_path = os.path.join(l2tdevtools_path, u'data')
    self._dependency_definition = dependency_definition

  def CheckBuildDependencies(self):
    """Checks if the build dependencies are met.

    Returns:
      A list of build dependency names that are not met or an empty list.
    """
    return list(self._dependency_definition.build_dependencies)

  def CheckBuildRequired(self, unused_source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if a build is required, False otherwise.
    """
    return True


class DpkgBuildHelper(BuildHelper):
  """Class that helps in building dpkg packages (.deb)."""

  _BUILD_DEPENDENCIES = frozenset([
      u'git',
      u'build-essential',
      u'autotools-dev',
      u'autoconf',
      u'automake',
      u'autopoint',
      u'libtool',
      u'gettext',
      u'flex',
      u'byacc',
      u'debhelper',
      u'devscripts',
      u'dpkg-dev',
      u'fakeroot',
      u'quilt',
      u'python-dev',
      u'python-setuptools'
  ])

  _BUILD_DEPENDENCY_PACKAGE_NAMES = {
      u'bzip2': u'libbz2-dev',
      u'fuse': u'libfuse-dev',
      u'libcrypto': u'libssl-dev',
      u'sqlite': u'libsqlite3-dev',
      u'zeromq': u'libzmq3-dev',
      u'zlib': u'zlib1g-dev'
  }

  def __init__(self, dependency_definition, l2tdevtools_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      l2tdevtools_path: the path to the l2tdevtools directory.
    """
    super(DpkgBuildHelper, self).__init__(
        dependency_definition, l2tdevtools_path)
    self._prep_script = u'prep-dpkg.sh'
    self._post_script = u'post-dpkg.sh'

  def _BuildPrepare(
      self, source_directory, project_name, project_version, version_suffix,
      distribution, architecture):
    """Make the necessary preparations before building the dpkg packages.

    Args:
      source_directory: the name of the source directory.
      project_name: the name of the project.
      project_version: the version of the project.
      version_suffix: the version suffix.
      distribution: the distribution.
      architecture: the architecture.

    Returns:
      True if the preparations were successful, False otherwise.
    """
    # Script to run before building, e.g. to change the dpkg packaging files.
    if os.path.exists(self._prep_script):
      command = u'sh ../{0:s} {1:s} {2!s} {3:s} {4:s} {5:s}'.format(
          self._prep_script, project_name, project_version, version_suffix,
          distribution, architecture)
      exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
          source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

    return True

  def _BuildFinalize(
      self, source_directory, project_name, project_version, version_suffix,
      distribution, architecture):
    """Make the necessary finalizations after building the dpkg packages.

    Args:
      source_directory: the name of the source directory.
      project_name: the name of the project.
      project_version: the version of the project.
      version_suffix: the version suffix.
      distribution: the distribution.
      architecture: the architecture.

    Returns:
      True if the finalizations were successful, False otherwise.
    """
    # Script to run after building, e.g. to automatically upload the dpkg
    # package files to an apt repository.
    if os.path.exists(self._post_script):
      command = u'sh ../{0:s} {1:s} {2!s} {3:s} {4:s} {5:s}'.format(
          self._post_script, project_name, project_version, version_suffix,
          distribution, architecture)
      exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
          source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

    return True

  def _CheckIsInstalled(self, package_name):
    """Checks if a package is installed.

    Args:
      package_name: the name of the package.

    Returns:
      A boolean value containing true if the package is installed
      false otherwise.
    """
    command = u'dpkg-query -s {0:s} >/dev/null 2>&1'.format(package_name)
    exit_code = subprocess.call(command, shell=True)
    return exit_code == 0

  def CheckBuildDependencies(self):
    """Checks if the build dependencies are met.

    Returns:
      A list of build dependency names that are not met or an empty list.
    """
    missing_packages = []
    for package_name in self._BUILD_DEPENDENCIES:
      if not self._CheckIsInstalled(package_name):
        missing_packages.append(package_name)

    for package_name in self._dependency_definition.build_dependencies:
      package_name = self._BUILD_DEPENDENCY_PACKAGE_NAMES.get(
          package_name, package_name)
      if not self._CheckIsInstalled(package_name):
        missing_packages.append(package_name)

      if package_name not in (
          self._dependency_definition.dpkg_build_dependencies):
        self._dependency_definition.dpkg_build_dependencies.append(
            package_name)

    return missing_packages


class ConfigureMakeDpkgBuildHelper(DpkgBuildHelper):
  """Class that helps in building dpkg packages (.deb)."""

  _VERSION_GLOB = u'[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'

  def __init__(self, dependency_definition, l2tdevtools_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      l2tdevtools_path: the path to the l2tdevtools directory.
    """
    super(ConfigureMakeDpkgBuildHelper, self).__init__(
        dependency_definition, l2tdevtools_path)
    self.architecture = platform.machine()
    self.distribution = u''
    self.version_suffix = u''

    if self.architecture == u'i686':
      self.architecture = u'i386'
    elif self.architecture == u'x86_64':
      self.architecture = u'amd64'

  def Build(self, source_helper_object):
    """Builds the dpkg packages.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    # dpkg-buildpackage wants an source package filename without
    # the status indication and orig indication.
    deb_orig_source_filename = u'{0:s}_{1!s}.orig.tar.gz'.format(
        source_helper_object.project_name, source_helper_object.project_version)
    shutil.copy(source_filename, deb_orig_source_filename)

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building deb of: {0:s}'.format(source_filename))

    dpkg_directory = os.path.join(source_directory, u'dpkg')
    if not os.path.exists(dpkg_directory):
      dpkg_directory = os.path.join(source_directory, u'config', u'dpkg')

    if not os.path.exists(dpkg_directory):
      # Generate the dpkg build files if necessary.
      os.chdir(source_directory)

      build_files_generator = dpkg_files.DpkgBuildFilesGenerator(
          source_helper_object.project_name,
          source_helper_object.project_version, self._dependency_definition,
          self._data_path)
      build_files_generator.GenerateFiles(u'dpkg')

      os.chdir(u'..')

      dpkg_directory = os.path.join(source_directory, u'dpkg')

    if not os.path.exists(dpkg_directory):
      logging.error(u'Missing dpkg sub directory in: {0:s}'.format(
          source_directory))
      return False

    debian_directory = os.path.join(source_directory, u'debian')

    # If there is a debian directory remove it and recreate it from
    # the dpkg directory.
    if os.path.exists(debian_directory):
      logging.info(u'Removing: {0:s}'.format(debian_directory))
      shutil.rmtree(debian_directory)
    shutil.copytree(dpkg_directory, debian_directory)

    if not self._BuildPrepare(
        source_directory, source_helper_object.project_name,
        source_helper_object.project_version, self.version_suffix,
        self.distribution, self.architecture):
      return False

    command = u'dpkg-buildpackage -uc -us -rfakeroot > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    if not self._BuildFinalize(
        source_directory, source_helper_object.project_name,
        source_helper_object.project_version, self.version_suffix,
        self.distribution, self.architecture):
      return False

    return True

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if a build is required, False otherwise.
    """
    deb_filename = u'{0:s}_{1!s}-1_{2:s}.deb'.format(
        source_helper_object.project_name,
        source_helper_object.project_version, self.architecture)

    return not os.path.exists(deb_filename)

  def Clean(self, source_helper_object):
    """Cleans the dpkg packages in the current directory.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).
    """
    filenames_to_ignore = re.compile(u'^{0:s}_{1!s}.orig.tar.gz'.format(
        source_helper_object.project_name,
        source_helper_object.project_version))

    # Remove files of previous versions in the format:
    # project_version.orig.tar.gz
    filenames = glob.glob(u'{0:s}_{1:s}.orig.tar.gz'.format(
        source_helper_object.project_name, self._VERSION_GLOB))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_to_ignore = re.compile(u'^{0:s}[-_].*{1!s}'.format(
        source_helper_object.project_name,
        source_helper_object.project_version))

    # Remove files of previous versions in the format:
    # project[-_]version-1_architecture.*
    filenames = glob.glob(u'{0:s}[-_]*{1:s}-1_{2:s}.*'.format(
        source_helper_object.project_name, self._VERSION_GLOB,
        self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # project[-_]*version-1.*
    filenames = glob.glob(u'{0:s}[-_]*{1:s}-1.*'.format(
        source_helper_object.project_name, self._VERSION_GLOB))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)


class ConfigureMakeSourceDpkgBuildHelper(DpkgBuildHelper):
  """Class that helps in building source dpkg packages (.deb)."""

  _VERSION_GLOB = u'[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'

  def __init__(self, dependency_definition, l2tdevtools_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      l2tdevtools_path: the path to the l2tdevtools directory.
    """
    super(ConfigureMakeSourceDpkgBuildHelper, self).__init__(
        dependency_definition, l2tdevtools_path)
    self._prep_script = u'prep-dpkg-source.sh'
    self._post_script = u'post-dpkg-source.sh'
    self.architecture = u'source'
    self.distribution = u'trusty'
    self.version_suffix = u'ppa1'

  def Build(self, source_helper_object):
    """Builds the dpkg packages.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    # dpkg-buildpackage wants an source package filename without
    # the status indication and orig indication.
    deb_orig_source_filename = u'{0:s}_{1!s}.orig.tar.gz'.format(
        source_helper_object.project_name, source_helper_object.project_version)
    shutil.copy(source_filename, deb_orig_source_filename)

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building source deb of: {0:s}'.format(source_filename))

    dpkg_directory = os.path.join(source_directory, u'dpkg')
    if not os.path.exists(dpkg_directory):
      dpkg_directory = os.path.join(source_directory, u'config', u'dpkg')

    if not os.path.exists(dpkg_directory):
      # Generate the dpkg build files if necessary.
      os.chdir(source_directory)

      build_files_generator = dpkg_files.DpkgBuildFilesGenerator(
          source_helper_object.project_name,
          source_helper_object.project_version, self._dependency_definition,
          self._data_path)
      build_files_generator.GenerateFiles(u'dpkg')

      os.chdir(u'..')

      dpkg_directory = os.path.join(source_directory, u'dpkg')

    if not os.path.exists(dpkg_directory):
      logging.error(u'Missing dpkg sub directory in: {0:s}'.format(
          source_directory))
      return False

    debian_directory = os.path.join(source_directory, u'debian')

    # If there is a debian directory remove it and recreate it from
    # the dpkg directory.
    if os.path.exists(debian_directory):
      logging.info(u'Removing: {0:s}'.format(debian_directory))
      shutil.rmtree(debian_directory)
    shutil.copytree(dpkg_directory, debian_directory)

    if not self._BuildPrepare(
        source_directory, source_helper_object.project_name,
        source_helper_object.project_version, self.version_suffix,
        self.distribution, self.architecture):
      return False

    command = u'debuild -S -sa > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    if not self._BuildFinalize(
        source_directory, source_helper_object.project_name,
        source_helper_object.project_version, self.version_suffix,
        self.distribution, self.architecture):
      return False

    return True

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if a build is required, False otherwise.
    """
    changes_filename = u'{0:s}_{1!s}-1{2:s}~{3:s}_{4:s}.changes'.format(
        source_helper_object.project_name, source_helper_object.project_version,
        self.version_suffix, self.distribution, self.architecture)

    return not os.path.exists(changes_filename)

  def Clean(self, source_helper_object):
    """Cleans the dpkg packages in the current directory.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).
    """
    filenames_to_ignore = re.compile(u'^{0:s}_{1!s}.orig.tar.gz'.format(
        source_helper_object.project_name,
        source_helper_object.project_version))

    # Remove files of previous versions in the format:
    # project_version.orig.tar.gz
    filenames = glob.glob(u'{0:s}_{1:s}.orig.tar.gz'.format(
        source_helper_object.project_name, self._VERSION_GLOB))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_to_ignore = re.compile(u'^{0:s}[-_].*{1!s}'.format(
        source_helper_object.project_name,
        source_helper_object.project_version))

    # Remove files of previous versions in the format:
    # project[-_]version-1suffix~distribution_architecture.*
    filenames = glob.glob((u'{0:s}[-_]*{1:s}-1{2:s}~{3:s}_{4:s}.*').format(
        source_helper_object.project_name, self._VERSION_GLOB,
        self.version_suffix, self.distribution, self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # project[-_]*version-1suffix~distribution.*
    filenames = glob.glob((u'{0:s}[-_]*{1:s}-1{2:s}~{3:s}.*').format(
        source_helper_object.project_name, self._VERSION_GLOB,
        self.version_suffix, self.distribution))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)


class SetupPyDpkgBuildHelper(DpkgBuildHelper):
  """Class that helps in building dpkg packages (.deb)."""

  def __init__(self, dependency_definition, l2tdevtools_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      l2tdevtools_path: the path to the l2tdevtools directory.
    """
    super(SetupPyDpkgBuildHelper, self).__init__(
        dependency_definition, l2tdevtools_path)
    self.architecture = platform.machine()
    self.distribution = u''
    self.version_suffix = u''

    if not dependency_definition.architecture_dependent:
      self.architecture = u'all'
    elif self.architecture == u'i686':
      self.architecture = u'i386'
    elif self.architecture == u'x86_64':
      self.architecture = u'amd64'

  def Build(self, source_helper_object):
    """Builds the dpkg packages.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = source_helper_object.project_name
      if not project_name.startswith(u'python-'):
        project_name = u'python-{0:s}'.format(project_name)

    # dpkg-buildpackage wants an source package filename without
    # the status indication and orig indication.
    deb_orig_source_filename = u'{0:s}_{1!s}.orig.tar.gz'.format(
        project_name, source_helper_object.project_version)
    shutil.copy(source_filename, deb_orig_source_filename)

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building deb of: {0:s}'.format(source_filename))

    dpkg_directory = os.path.join(source_directory, u'dpkg')
    if not os.path.exists(dpkg_directory):
      dpkg_directory = os.path.join(source_directory, u'config', u'dpkg')

    if not os.path.exists(dpkg_directory):
      # Generate the dpkg build files if necessary.
      os.chdir(source_directory)

      # Pass the project name without the python- prefix.
      build_files_generator = dpkg_files.DpkgBuildFilesGenerator(
          source_helper_object.project_name,
          source_helper_object.project_version,
          self._dependency_definition, self._data_path)
      build_files_generator.GenerateFiles(u'dpkg')

      os.chdir(u'..')

      dpkg_directory = os.path.join(source_directory, u'dpkg')

    if not os.path.exists(dpkg_directory):
      logging.error(u'Missing dpkg sub directory in: {0:s}'.format(
          source_directory))
      return False

    debian_directory = os.path.join(source_directory, u'debian')

    # If there is a debian directory remove it and recreate it from
    # the dpkg directory.
    if os.path.exists(debian_directory):
      logging.info(u'Removing: {0:s}'.format(debian_directory))
      shutil.rmtree(debian_directory)
    shutil.copytree(dpkg_directory, debian_directory)

    if not self._BuildPrepare(
        source_directory, project_name, source_helper_object.project_version,
        self.version_suffix, self.distribution, self.architecture):
      return False

    command = u'dpkg-buildpackage -uc -us -rfakeroot > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    if not self._BuildFinalize(
        source_directory, project_name, source_helper_object.project_version,
        self.version_suffix, self.distribution, self.architecture):
      return False

    return True

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if a build is required, False otherwise.
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = source_helper_object.project_name
      if not project_name.startswith(u'python-'):
        project_name = u'python-{0:s}'.format(project_name)

    deb_filename = u'{0:s}_{1!s}-1_{2:s}.deb'.format(
        project_name, source_helper_object.project_version, self.architecture)

    return not os.path.exists(deb_filename)

  def Clean(self, source_helper_object):
    """Cleans the dpkg packages in the current directory.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = source_helper_object.project_name
      if not project_name.startswith(u'python-'):
        project_name = u'python-{0:s}'.format(project_name)

    filenames_to_ignore = re.compile(u'^{0:s}_{1!s}.orig.tar.gz'.format(
        project_name, source_helper_object.project_version))

    # Remove files of previous versions in the format:
    # project_version.orig.tar.gz
    filenames = glob.glob(u'{0:s}_*.orig.tar.gz'.format(project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_to_ignore = re.compile(u'^{0:s}[-_].*{1!s}'.format(
        project_name, source_helper_object.project_version))

    # Remove files of previous versions in the format:
    # project[-_]*version-1_architecture.*
    filenames = glob.glob(u'{0:s}[-_]*-1_{1:s}.*'.format(
        project_name, self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # project[-_]*version-1.*
    filenames = glob.glob(u'{0:s}[-_]*-1.*'.format(project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)


class SetupPySourceDpkgBuildHelper(DpkgBuildHelper):
  """Class that helps in building source dpkg packages (.deb)."""

  def __init__(self, dependency_definition, l2tdevtools_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      l2tdevtools_path: the path to the l2tdevtools directory.
    """
    super(SetupPySourceDpkgBuildHelper, self).__init__(
        dependency_definition, l2tdevtools_path)
    self._prep_script = u'prep-dpkg-source.sh'
    self._post_script = u'post-dpkg-source.sh'
    self.architecture = u'source'
    self.distribution = u'trusty'
    self.version_suffix = u'ppa1'

  def Build(self, source_helper_object):
    """Builds the dpkg packages.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = source_helper_object.project_name
      if not project_name.startswith(u'python-'):
        project_name = u'python-{0:s}'.format(project_name)

    # dpkg-buildpackage wants an source package filename without
    # the status indication and orig indication.
    deb_orig_source_filename = u'{0:s}_{1!s}.orig.tar.gz'.format(
        project_name, source_helper_object.project_version)
    shutil.copy(source_filename, deb_orig_source_filename)

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building source deb of: {0:s}'.format(source_filename))

    dpkg_directory = os.path.join(source_directory, u'dpkg')
    if not os.path.exists(dpkg_directory):
      dpkg_directory = os.path.join(source_directory, u'config', u'dpkg')

    if not os.path.exists(dpkg_directory):
      # Generate the dpkg build files if necessary.
      os.chdir(source_directory)

      # Pass the project name without the python- prefix.
      build_files_generator = dpkg_files.DpkgBuildFilesGenerator(
          source_helper_object.project_name,
          source_helper_object.project_version,
          self._dependency_definition, self._data_path)
      build_files_generator.GenerateFiles(u'dpkg')

      os.chdir(u'..')

      dpkg_directory = os.path.join(source_directory, u'dpkg')

    if not os.path.exists(dpkg_directory):
      logging.error(u'Missing dpkg sub directory in: {0:s}'.format(
          source_directory))
      return False

    debian_directory = os.path.join(source_directory, u'debian')

    # If there is a debian directory remove it and recreate it from
    # the dpkg directory.
    if os.path.exists(debian_directory):
      logging.info(u'Removing: {0:s}'.format(debian_directory))
      shutil.rmtree(debian_directory)
    shutil.copytree(dpkg_directory, debian_directory)

    if not self._BuildPrepare(
        source_directory, project_name, source_helper_object.project_version,
        self.version_suffix, self.distribution, self.architecture):
      return False

    command = u'debuild -S -sa > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    if not self._BuildFinalize(
        source_directory, project_name, source_helper_object.project_version,
        self.version_suffix, self.distribution, self.architecture):
      return False

    return True

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if a build is required, False otherwise.
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = source_helper_object.project_name
      if not project_name.startswith(u'python-'):
        project_name = u'python-{0:s}'.format(project_name)

    changes_filename = u'{0:s}_{1!s}-1{2:s}~{3:s}_{4:s}.changes'.format(
        project_name, source_helper_object.project_version,
        self.version_suffix, self.distribution, self.architecture)

    return not os.path.exists(changes_filename)

  def Clean(self, source_helper_object):
    """Cleans the dpkg packages in the current directory.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = source_helper_object.project_name
      if not project_name.startswith(u'python-'):
        project_name = u'python-{0:s}'.format(project_name)

    filenames_to_ignore = re.compile(u'^{0:s}_{1!s}.orig.tar.gz'.format(
        project_name, source_helper_object.project_version))

    # Remove files of previous versions in the format:
    # project_version.orig.tar.gz
    filenames = glob.glob(u'{0:s}_*.orig.tar.gz'.format(project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_to_ignore = re.compile(u'^{0:s}[-_].*{1!s}'.format(
        project_name, source_helper_object.project_version))

    # Remove files of previous versions in the format:
    # project[-_]*version-1suffix~distribution_architecture.*
    filenames = glob.glob(u'{0:s}[-_]*-1{1:s}~{2:s}_{3:s}.*'.format(
        project_name, self.version_suffix, self.distribution,
        self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # project[-_]*version-1suffix~distribution.*
    filenames = glob.glob(u'{0:s}[-_]*-1{1:s}~{2:s}.*'.format(
        project_name, self.version_suffix, self.distribution))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)


class MsiBuildHelper(BuildHelper):
  """Class that helps in building Microsoft Installer packages (.msi)."""

  def __init__(self, dependency_definition, l2tdevtools_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      l2tdevtools_path: the path to the l2tdevtools directory.
    """
    super(MsiBuildHelper, self).__init__(
        dependency_definition, l2tdevtools_path)
    self.architecture = platform.machine()

    if self.architecture == u'x86':
      self.architecture = u'win32'
    elif self.architecture == u'AMD64':
      self.architecture = u'win-amd64'

  def _ApplyPatches(self, patches):
    """Applies patches.

    Args:
      source_directory: the name of the source directory.
      patches: list of patch file names.

    Returns:
      A boolean value indicating if applying the patches was successful.
    """
    # Search common locations for patch.exe
    patch = u'{0:s}:{1:s}{2:s}'.format(
        u'C', os.sep, os.path.join(u'GnuWin', u'bin', u'patch.exe'))

    if not os.path.exists(patch):
      logging.error(u'Unable to find patch.exe')
      return False

    for patch_filename in patches:
      filename = os.path.join(self._data_path, u'patches', patch_filename)
      if not os.path.exists(filename):
        logging.warning(u'Missing patch file: {0:s}'.format(filename))
        continue

      command = u'{0:s} --force --binary --input {1:s}'.format(patch, filename)
      exit_code = subprocess.call(command, shell=False)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

    return True


class ConfigureMakeMsiBuildHelper(MsiBuildHelper):
  """Class that helps in building Microsoft Installer packages (.msi)."""

  def __init__(self, dependency_definition, l2tdevtools_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      l2tdevtools_path: the path to the l2tdevtools directory.

    Raises:
      RuntimeError: if the Visual Studio version could be determined or
                    msvscpp-convert.py could not be found.
    """
    super(ConfigureMakeMsiBuildHelper, self).__init__(
        dependency_definition, l2tdevtools_path)

    if u'VS140COMNTOOLS' in os.environ:
      self.version = u'2015'

    elif u'VS120COMNTOOLS' in os.environ:
      self.version = u'2013'

    elif u'VS110COMNTOOLS' in os.environ:
      self.version = u'2012'

    elif u'VS100COMNTOOLS' in os.environ:
      self.version = u'2010'

    # Since the script exports VS90COMNTOOLS to the environment we need
    # to check the other Visual Studio environment variables first.
    elif u'VS90COMNTOOLS' in os.environ:
      self.version = u'2008'

    else:
      raise RuntimeError(u'Unable to determine Visual Studio version.')

    if self.version != u'2008':
      self._msvscpp_convert = os.path.join(
          l2tdevtools_path, u'tools', u'msvscpp-convert.py')

      if not os.path.exists(self._msvscpp_convert):
        raise RuntimeError(u'Unable to find msvscpp-convert.py')

  def _BuildMSBuild(self, source_helper_object, source_directory):
    """Builds using Visual Studio and MSBuild.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).
      source_directory: the name of the source directory.

    Returns:
      True if successful, False otherwise.
    """
    # Search common locations for MSBuild.exe
    if self.version == u'2008':
      msbuild = u'{0:s}:{1:s}{2:s}'.format(
          u'C', os.sep, os.path.join(
              u'Windows', u'Microsoft.NET', u'Framework', u'v3.5',
              u'MSBuild.exe'))

    # Note that MSBuild in .NET 3.5 does not support vs2010 solution files
    # and MSBuild in .NET 4.0 is needed instead.
    elif self.version in [u'2010', u'2012', u'2013', u'2015']:
      msbuild = u'{0:s}:{1:s}{2:s}'.format(
          u'C', os.sep, os.path.join(
              u'Windows', u'Microsoft.NET', u'Framework', u'v4.0.30319',
              u'MSBuild.exe'))

    else:
      msbuild = u''

    if not msbuild or not os.path.exists(msbuild):
      logging.error(u'Unable to find MSBuild.exe')
      return False

    if self.version == u'2008':
      if not os.environ[u'VS90COMNTOOLS']:
        logging.error(u'Missing VS90COMNTOOLS environment variable.')
        return False

    elif self.version == u'2010':
      if not os.environ[u'VS100COMNTOOLS']:
        logging.error(u'Missing VS100COMNTOOLS environment variable.')
        return False

    elif self.version == u'2012':
      if not os.environ[u'VS110COMNTOOLS']:
        logging.error(u'Missing VS110COMNTOOLS environment variable.')
        return False

    elif self.version == u'2013':
      if not os.environ[u'VS120COMNTOOLS']:
        logging.error(u'Missing VS120COMNTOOLS environment variable.')
        return False

    elif self.version == u'2015':
      if not os.environ[u'VS140COMNTOOLS']:
        logging.error(u'Missing VS140COMNTOOLS environment variable.')
        return False

    zlib_project_file = os.path.join(
        source_directory, u'msvscpp', u'zlib', u'zlib.vcproj')
    zlib_source_directory = os.path.join(
        os.path.dirname(source_directory), u'zlib')

    if (os.path.exists(zlib_project_file) and
        not os.path.exists(zlib_source_directory)):
      logging.error(u'Missing dependency: zlib.')
      return False

    dokan_project_file = os.path.join(
        source_directory, u'msvscpp', u'dokan', u'dokan.vcproj')
    dokan_source_directory = os.path.join(
        os.path.dirname(source_directory), u'dokan')

    if (os.path.exists(dokan_project_file) and
        not os.path.exists(dokan_source_directory)):
      logging.error(u'Missing dependency: dokan.')
      return False

    # For the Visual Studio builds later than 2008 the convert the 2008
    # solution and project files need to be converted to the newer version.
    if self.version in [u'2010', u'2012', u'2013', u'2015']:
      self._ConvertSolutionFiles(source_directory)

    # Detect architecture based on Visual Studion Platform environment
    self._BuildPrepare(source_helper_object, source_directory)

    # variable. If not set the platform with default to Win32.
    msvscpp_platform = os.environ.get(u'Platform', None)
    if not msvscpp_platform:
      msvscpp_platform = os.environ.get(u'TARGET_CPU', None)

    if not msvscpp_platform or msvscpp_platform == u'x86':
      msvscpp_platform = u'Win32'

    if msvscpp_platform not in [u'Win32', u'x64']:
      logging.error(u'Unsupported build platform: {0:s}'.format(
          msvscpp_platform))
      return False

    if self.version == u'2008' and msvscpp_platform == u'x64':
      logging.error(u'Unsupported 64-build platform for vs2008.')
      return False

    solution_filenames = glob.glob(os.path.join(
        source_directory, u'msvscpp', u'*.sln'))
    if len(solution_filenames) != 1:
      logging.error(u'Unable to find Visual Studio solution file')
      return False

    solution_filename = solution_filenames[0]

    command = (
        u'{0:s} /p:Configuration=Release /p:Platform={1:s} /noconsolelogger '
        u'/fileLogger /maxcpucount {2:s}').format(
            msbuild, msvscpp_platform, solution_filename)
    exit_code = subprocess.call(command, shell=False)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    python_module_name, _, _ = source_directory.partition(u'-')
    python_module_name = u'py{0:s}'.format(python_module_name[3:])
    python_module_directory = os.path.join(
        source_directory, python_module_name)
    python_module_dist_directory = os.path.join(
        python_module_directory, u'dist')

    if os.path.exists(python_module_dist_directory):
      return True

    build_directory = os.path.join(u'..', u'..')

    os.chdir(python_module_directory)

    result = self._BuildSetupPy()
    if result:
      result = self._MoveMsi(python_module_name, build_directory)

    os.chdir(build_directory)

    return result

  def _BuildPrepare(self, source_helper_object, source_directory):
    """Prepares the source for building with Visual Studio.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).
      source_directory: the name of the source directory.
    """
    # For the vs2008 build make sure the binary is XP compatible,
    # by setting WINVER to 0x0501. For the vs2010 build WINVER is
    # set to 0x0600 (Windows Vista).

    # WINVER is set in common\config_winapi.h or common\config_msc.h.
    config_filename = os.path.join(
        source_directory, u'common', u'config_winapi.h')

    # If the WINAPI configuration file is not available use
    # the MSC compiler configuration file instead.
    if not os.path.exists(config_filename):
      config_filename = os.path.join(
          source_directory, u'common', u'config_msc.h')

    # Add a line to the config file that sets WINVER.
    parsing_mode = 0

    for line in fileinput.input(config_filename, inplace=1):
      # Remove trailing whitespace and end-of-line characters.
      line = line.rstrip()

      if parsing_mode != 2 or line:
        if parsing_mode == 1:
          # TODO: currently we want libbde not use Windows Crypto API, hence
          # we set WINVER to 0x0501.
          if (self.version == u'2008' or
              source_helper_object.project_name == u'libbde'):
            if not line.startswith(b'#define WINVER 0x0501'):
              print(b'#define WINVER 0x0501')
              print(b'')

          else:
            if not line.startswith(b'#define WINVER 0x0600'):
              print(b'#define WINVER 0x0600')
              print(b'')

          parsing_mode = 2

        elif line.startswith(b'#define _CONFIG_'):
          parsing_mode = 1

      print(line)

  def _BuildSetupPy(self):
    """Builds using Visual Studio and setup.py.

    This function assumes setup.py is present in the current working
    directory.

    Returns:
      True if successful, False otherwise.
    """
    # Setup.py uses VS90COMNTOOLS which is vs2008 specific
    # so we need to set it for the other Visual Studio versions.
    if self.version == u'2010':
      os.environ[u'VS90COMNTOOLS'] = os.environ[u'VS100COMNTOOLS']

    elif self.version == u'2012':
      os.environ[u'VS90COMNTOOLS'] = os.environ[u'VS110COMNTOOLS']

    elif self.version == u'2013':
      os.environ[u'VS90COMNTOOLS'] = os.environ[u'VS120COMNTOOLS']

    elif self.version == u'2015':
      os.environ[u'VS90COMNTOOLS'] = os.environ[u'VS140COMNTOOLS']

    command = u'{0:s} setup.py bdist_msi'.format(sys.executable)
    exit_code = subprocess.call(command, shell=False)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _ConvertSolutionFiles(self, source_directory):
    """Converts the Visual Studio solution and project files.

    Args:
      source_directory: the name of the source directory.
    """
    logging.info(u'Converting Visual Studio solution and project files.')
    os.chdir(source_directory)

    solution_filenames = glob.glob(os.path.join(u'msvscpp', u'*.sln'))
    if len(solution_filenames) != 1:
      logging.error(u'Unable to find Visual Studio solution file')
      return False

    solution_filename = solution_filenames[0]

    if not os.path.exists(u'vs2008'):
      command = u'{0:s} {1:s} --to {2:s} {3:s}'.format(
          sys.executable, self._msvscpp_convert, self.version,
          solution_filename)
      exit_code = subprocess.call(command, shell=False)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      # Note that setup.py needs the Visual Studio solution directory
      # to be named: msvscpp. So replace the Visual Studio 2008 msvscpp
      # solution directory with the converted one.
      os.rename(u'msvscpp', u'vs2008')
      os.rename(u'vs{0:s}'.format(self.version), u'msvscpp')

    os.chdir(u'..')

  def _MoveMsi(self, python_module_name, build_directory):
    """Moves the MSI from the dist sub directory into the build directory.

    Args:
      python_module_name: the Python module name.
      build_directory: the build directory.

    Returns:
      True if the move was successful, False otherwise.
    """
    msi_filename = os.path.join(
        u'dist', u'{0:s}-*.msi'.format(python_module_name))
    msi_glob = glob.glob(msi_filename)
    if len(msi_glob) != 1:
      logging.error(u'Unable to find MSI file.')
      return False

    _, _, msi_filename = msi_glob[0].rpartition(os.path.sep)
    msi_filename = os.path.join(build_directory, msi_filename)
    if os.path.exists(msi_filename):
      logging.warning(u'MSI file already exists.')
    else:
      logging.info(u'Moving: {0:s}'.format(msi_glob[0]))
      shutil.move(msi_glob[0], build_directory)

    return True

  def _SetupBuildDependencyDokan(self):
    """Sets up the dokan build dependency.

    Returns:
      True if successful, False otherwise.
    """
    # TODO: implement.
    return False

  def _SetupBuildDependencySqlite(self):
    """Sets up the sqlite build dependency.

    Returns:
      True if successful, False otherwise.
    """
    # TODO: download and build sqlite3 from source
    # http://www.sqlite.org/download.html
    # copy sqlite3.h to <source>/src/ directory?
    # copy .lib and .dll to <source>/ directory?
    # bundle .dll

    # <a id='a3' href='hp1.html'>sqlite-amalgamation-3081002.zip
    # d391('a3','2015/sqlite-amalgamation-3081002.zip');
    # http://www.sqlite.org/2015/sqlite-amalgamation-3081002.zip

    # Create msvscpp files and build dll
    return False

  def _SetupBuildDependencyZeroMQ(self):
    """Sets up the zeromq build dependency.

    Returns:
      True if successful, False otherwise.
    """
    # TODO: implement.
    return False

  def _SetupBuildDependencyZlib(self):
    """Sets up the zlib build dependency.

    Returns:
      True if successful, False otherwise.
    """
    download_helper_object = download_helper.SourceForgeDownloadHelper()
    source_helper_object = source_helper.SourcePackageHelper(
        u'zlib', download_helper_object)

    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(
              source_filename))
      return False

    if not os.path.exists(u'zlib'):
      os.rename(source_directory, u'zlib')

    return True

  def CheckBuildDependencies(self):
    """Checks if the build dependencies are met.

    Returns:
      A list of build dependency names that are not met or an empty list.
    """
    missing_packages = []
    for package_name in self._dependency_definition.build_dependencies:
      if package_name == u'fuse':
        self._SetupBuildDependencyDokan()

      elif package_name == u'sqlite':
        self._SetupBuildDependencySqlite()

      elif package_name == u'zeromq':
        self._SetupBuildDependencyZeroMQ()

      elif package_name == u'zlib':
        self._SetupBuildDependencyZlib()

      elif package_name != u'libcrypto':
        missing_packages.append(package_name)

    return missing_packages

  def Build(self, source_helper_object):
    """Builds using Visual Studio.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building: {0:s} with Visual Studio {1:s}'.format(
        source_filename, self.version))

    if self._dependency_definition.patches:
      os.chdir(source_directory)
      result = self._ApplyPatches(self._dependency_definition.patches)
      os.chdir(u'..')

      if not result:
        return False

    result = False

    setup_py_path = os.path.join(source_directory, u'setup.py')
    if not os.path.exists(setup_py_path):
      result = self._BuildMSBuild(source_helper_object, source_directory)

    else:
      python_module_name, _, _ = source_directory.partition(u'-')
      python_module_dist_directory = os.path.join(source_directory, u'dist')

      if not os.path.exists(python_module_dist_directory):
        build_directory = os.path.join(u'..')

        os.chdir(source_directory)

        result = self._BuildSetupPy()
        if result:
          result = self._MoveMsi(python_module_name, build_directory)

        os.chdir(build_directory)

    return result

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if a build is required, False otherwise.
    """
    msi_filename = u'{0:s}-python-{1!s}.1.{2:s}-py2.7.msi'.format(
        source_helper_object.project_name, source_helper_object.project_version,
        self.architecture)

    return not os.path.exists(msi_filename)

  def Clean(self, source_helper_object):
    """Cleans the build and dist directory.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).
    """
    # Remove previous versions of MSIs.
    filenames_to_ignore = re.compile(
        u'py{0:s}-.*{1!s}.1.{2:s}-py2.7.msi'.format(
            source_helper_object.project_name[3:],
            source_helper_object.project_version, self.architecture))

    msi_filenames_glob = u'py{0:s}-*.1.{1:s}-py2.7.msi'.format(
        source_helper_object.project_name[3:], self.architecture)

    filenames = glob.glob(msi_filenames_glob)
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_to_ignore = re.compile(
        u'{0:s}-python-.*{1!s}.1.{2:s}-py2.7.msi'.format(
            source_helper_object.project_name,
            source_helper_object.project_version, self.architecture))

    msi_filenames_glob = u'{0:s}-python-*.1.{1:s}-py2.7.msi'.format(
        source_helper_object.project_name, self.architecture)

    filenames = glob.glob(msi_filenames_glob)
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)


class SetupPyMsiBuildHelper(MsiBuildHelper):
  """Class that helps in building Microsoft Installer packages (.msi)."""

  def _GetFilenameSafeProjectInformation(self, source_helper_object):
    """Determines the filename safe project name and version.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      A tuple containing the filename safe project name and version.
    """
    if self._dependency_definition.setup_name:
      project_name = self._dependency_definition.setup_name
    else:
      project_name = source_helper_object.project_name

    if source_helper_object.project_name == u'dfvfs':
      project_version = u'{0!s}.1'.format(source_helper_object.project_version)
    else:
      project_version = u'{0!s}'.format(source_helper_object.project_version)

    return project_name, project_version

  def Build(self, source_helper_object):
    """Builds the msi.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building msi of: {0:s}'.format(source_filename))

    if self._dependency_definition.patches:
      os.chdir(source_directory)
      result = self._ApplyPatches(self._dependency_definition.patches)
      os.chdir(u'..')

      if not result:
        return False

    command = u'{0:s} setup.py bdist_msi > {1:s} 2>&1'.format(
        sys.executable, os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    # Move the msi to the build directory.
    project_name, _ = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    msi_filename = os.path.join(
        source_directory, u'dist', u'{0:s}-*.msi'.format(project_name))
    msi_glob = glob.glob(msi_filename)
    if len(msi_glob) != 1:
      logging.error(u'Unable to find MSI file.')
      return False

    _, _, msi_filename = msi_glob[0].rpartition(os.path.sep)
    if os.path.exists(msi_filename):
      logging.warning(u'MSI file already exists.')
    else:
      logging.info(u'Moving: {0:s}'.format(msi_glob[0]))
      shutil.move(msi_glob[0], u'.')

    return True

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if a build is required, False otherwise.
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    # TODO: it looks like coverage is no architecture dependent on Windows.
    # Check if it is architecture dependent on other platforms.
    if (self._dependency_definition.architecture_dependent and
        project_name != u'coverage'):
      suffix = u'-py2.7'
    else:
      suffix = u''

    # MSI does not support a single number version therefore we add '.1'.
    if u'.' not in project_version:
      project_version = u'{0!s}.1'.format(project_version)

    # MSI does not support a 4 digit version, e.g. '1.2.3.4' therefore
    # we remove the last digit.
    elif len(project_version.split(u'.')) == 4:
      project_version, _, _ = project_version.rpartition(u'.')

    # MSI does not support a version containing a '-', e.g. '1.2.3-4'
    # therefore we remove the digit after the '-'.
    elif u'-' in project_version:
      project_version, _, _ = project_version.rpartition(u'-')

    msi_filename = u'{0:s}-{1:s}.{2:s}{3:s}.msi'.format(
        project_name, project_version, self.architecture, suffix)

    return not os.path.exists(msi_filename)

  def Clean(self, source_helper_object):
    """Cleans the build and dist directory.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).
    """
    # Remove previous versions build directories.
    for filename in [u'build', u'dist']:
      if os.path.exists(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        shutil.rmtree(filename, True)

    # Remove previous versions of MSIs.
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    if self._dependency_definition.architecture_dependent:
      suffix = u'-py2.7'
    else:
      suffix = u''

    # MSI does not support a single number version therefore we add '.1'.
    if u'.' not in project_version:
      project_version = u'{0!s}.1'.format(project_version)

    # MSI does not support a 4 digit version, e.g. '1.2.3.4' there we remove
    # the last digit.
    elif len(project_version.split(u'.')) == 4:
      project_version, _, _ = project_version.rpartition(u'.')

    # MSI does not support a version containing a '-', e.g. '1.2.3-4' there
    # we remove the digit after the '-'.
    elif u'-' in project_version:
      project_version, _, _ = project_version.rpartition(u'-')

    filenames_to_ignore = re.compile(u'{0:s}-.*{1!s}.{2:s}{3:s}.msi'.format(
        project_name, project_version, self.architecture, suffix))

    msi_filenames_glob = u'{0:s}-*.{1:s}{2:s}.msi'.format(
        project_name, self.architecture, suffix)

    filenames = glob.glob(msi_filenames_glob)
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)


class OscBuildHelper(BuildHelper):
  """Class that helps in building with osc for the openSUSE build service."""

  _OSC_PROJECT = u'home:joachimmetz:testing'

  _OSC_PACKAGE_METADATA = (
      u'<package name="{name:s}" project="{project:s}">\n'
      u'  <title>{title:s}</title>\n'
      u'  <description>{description:s}</description>\n'
      u'</package>\n')

  def _BuildPrepare(self, source_helper_object):
    """Prepares the source for building with osc.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).
    """
    # Checkout the project if it does not exist otherwise make sure
    # the project files are up to date.
    if not os.path.exists(self._OSC_PROJECT):
      if not self._OscCheckout():
        return

    else:
      if not self._OscUpdate():
        return False

    # Create a package of the project if it does not exist.
    osc_package_path = os.path.join(
        self._OSC_PROJECT, source_helper_object.project_name)
    if os.path.exists(osc_package_path):
      return True

    if not self._OscCreatePackage(source_helper_object):
      return False

    if not self._OscUpdate():
      return False

    return True

  def _CheckStatusIsClean(self):
    """Runs osc status to check if the status is clean.

    Returns:
      True if successful, False otherwise.
    """
    command = u'osc status {0:s}'.format(self._OSC_PROJECT)
    arguments = shlex.split(command)
    process = subprocess.Popen(
        arguments, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if not process:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    output, error = process.communicate()
    if process.returncode != 0:
      logging.error(u'Running: "{0:s}" failed with error: {1:s}.'.format(
          command, error))
      return False

    if len(output):
      logging.error(u'Unable to continue with pending changes.')
      return False

    return True

  def _OscAdd(self, path):
    """Runs osc add to add a new file.

    Args:
      path: string containing the path of the file to add, relative to
            the osc project directory.

    Returns:
      True if successful, False otherwise.
    """
    command = u'osc -q add {0:s}'.format(path)
    exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
        self._OSC_PROJECT, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _OscCheckout(self):
    """Runs osc checkout.

    Returns:
      True if successful, False otherwise.
    """
    command = u'osc -q checkout {0:s}'.format(self._OSC_PROJECT)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _OscCommit(self):
    """Runs osc commit.

    Returns:
      True if successful, False otherwise.
    """
    command = u'osc -q commit -n'
    exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
        self._OSC_PROJECT, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _OscCreatePackage(self, source_helper_object):
    """Runs osc meta pkg to create a new package.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if successful, False otherwise.
    """
    template_values = {
        u'description': source_helper_object.project_name,
        u'name': source_helper_object.project_name,
        u'project': self._OSC_PROJECT,
        u'title': source_helper_object.project_name}

    package_metadata = self._OSC_PACKAGE_METADATA.format(**template_values)

    command = (
        u'osc -q meta pkg -F - {0:s} {1:s} << EOI\n{2:s}\nEOI\n').format(
            self._OSC_PROJECT, source_helper_object.project_name,
            package_metadata)
    exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
        self._OSC_PROJECT, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _OscUpdate(self):
    """Runs osc update.

    Returns:
      True if successful, False otherwise.
    """
    command = u'osc -q update'
    exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
        self._OSC_PROJECT, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def CheckBuildDependencies(self):
    """Checks if the build dependencies are met.

    Returns:
      A list of build dependency names that are not met or an empty list.
    """
    # Dependencies are handled by the openSUSE build service.
    return []


class ConfigureMakeOscBuildHelper(OscBuildHelper):
  """Class that helps in building with osc for the openSUSE build service."""

  def Build(self, source_helper_object):
    """Builds the osc package.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    logging.info(u'Preparing osc build of: {0:s}'.format(source_filename))

    if not self._BuildPrepare(source_helper_object):
      return False

    osc_package_path = os.path.join(
        self._OSC_PROJECT, source_helper_object.project_name)

    # osc wants the project filename without the status indication.
    osc_source_filename = u'{0:s}-{1!s}.tar.gz'.format(
        source_helper_object.project_name,
        source_helper_object.project_version)

    # Copy the source package to the package directory.
    osc_source_path = os.path.join(osc_package_path, osc_source_filename)
    shutil.copy(source_filename, osc_source_path)

    osc_source_path = os.path.join(
        source_helper_object.project_name, osc_source_filename)
    if not self._OscAdd(osc_source_path):
      return False

    # Extract the build files from the source package into the package
    # directory.
    spec_filename = u'{0:s}.spec'.format(source_helper_object.project_name)

    osc_spec_file_path = os.path.join(osc_package_path, spec_filename)
    spec_file_exists = os.path.exists(osc_spec_file_path)

    command = u'tar xfO {0:s} {1:s}-{2!s}/{3:s} > {3:s}'.format(
        osc_source_filename, source_helper_object.project_name,
        source_helper_object.project_version, spec_filename)
    exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
        osc_package_path, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    if not spec_file_exists:
      osc_spec_file_path = os.path.join(
          source_helper_object.project_name, spec_filename)
      if not self._OscAdd(osc_spec_file_path):
        return False

    return self._OscCommit()

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if a build is required, False otherwise.
    """
    osc_source_filename = u'{0:s}-{1!s}.tar.gz'.format(
        source_helper_object.project_name,
        source_helper_object.project_version)

    osc_source_path = os.path.join(
        self._OSC_PROJECT, source_helper_object.project_name,
        osc_source_filename)

    return not os.path.exists(osc_source_path)

  def Clean(self, source_helper_object):
    """Cleans the build and dist directory.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).
    """
    osc_package_path = os.path.join(
        self._OSC_PROJECT, source_helper_object.project_name)
    osc_source_filename = u'{0:s}-{1!s}.tar.gz'.format(
        source_helper_object.project_name,
        source_helper_object.project_version)

    filenames_to_ignore = re.compile(u'^{0:s}'.format(
        os.path.join(osc_package_path, osc_source_filename)))

    # Remove files of previous versions in the format:
    # project-version.tar.gz
    osc_source_filename_glob = u'{0:s}-*.tar.gz'.format(
        source_helper_object.project_name)
    filenames = glob.glob(os.path.join(
        osc_package_path, osc_source_filename_glob))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))

        command = u'osc -q remove {0:s}'.format(os.path.basename(filename))
        exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
            osc_package_path, command), shell=True)
        if exit_code != 0:
          logging.error(u'Running: "{0:s}" failed.'.format(command))


class SetupPyOscBuildHelper(OscBuildHelper):
  """Class that helps in building with osc for the openSUSE build service."""

  def Build(self, source_helper_object):
    """Builds the osc package.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    logging.info(u'Preparing osc build of: {0:s}'.format(source_filename))

    if not self._BuildPrepare(source_helper_object):
      return False

    osc_package_path = os.path.join(
        self._OSC_PROJECT, source_helper_object.project_name)

    # Copy the source package to the package directory.
    osc_source_path = os.path.join(osc_package_path, source_filename)
    shutil.copy(source_filename, osc_source_path)

    osc_source_path = os.path.join(
        source_helper_object.project_name, source_filename)
    if not self._OscAdd(osc_source_path):
      return False

    # Have setup.py generate the .spec file.
    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    command = u'{0:s} setup.py bdist_rpm --spec-only > {1:s} 2>&1'.format(
        sys.executable, os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    spec_filename = u'{0:s}.spec'.format(source_helper_object.project_name)
    spec_file_path = os.path.join(source_directory, u'dist', spec_filename)
    osc_spec_file_path = os.path.join(osc_package_path, spec_filename)
    spec_file_exists = os.path.exists(osc_spec_file_path)

    # TODO: check if already prefixed with python-

    output_file_object = open(osc_spec_file_path, 'wb')
    description = b''
    summary = b''
    in_description = False
    with open(spec_file_path, 'r+b') as file_object:
      for line in file_object.readlines():
        if line.startswith(b'Summary: '):
          summary = line

        elif line.startswith(b'%description'):
          in_description = True

        elif line.startswith(b'%files'):
          line = b'%files -f INSTALLED_FILES -n python-%{name}\n'

        elif line.startswith(b'%prep'):
          in_description = False

          output_file_object.write((
              b'%package -n python-%{{name}}\n'
              b'{0:s}'
              b'\n'
              b'%description -n python-%{{name}}\n'
              b'{1:s}').format(summary, description))

        elif in_description:
          description = b''.join([description, line])

        output_file_object.write(line)

    output_file_object.close()

    if not spec_file_exists:
      osc_spec_file_path = os.path.join(
          source_helper_object.project_name, spec_filename)
      if not self._OscAdd(osc_spec_file_path):
        return False

    return self._OscCommit()

  def CheckBuildRequired(self, unused_source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if a build is required, False otherwise.
    """
    # TODO: implement.
    return True

  def Clean(self, unused_source_helper_object):
    """Cleans the source.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).
    """
    # TODO: implement.
    return


class PkgBuildHelper(BuildHelper):
  """Class that helps in building MacOS-X packages (.pkg)."""

  def __init__(self, dependency_definition, l2tdevtools_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      l2tdevtools_path: the path to the l2tdevtools directory.
    """
    super(PkgBuildHelper, self).__init__(
        dependency_definition, l2tdevtools_path)
    self._pkgbuild = os.path.join(u'/', u'usr', u'bin', u'pkgbuild')

  def _BuildDmg(self, pkg_filename, dmg_filename):
    """Builds the distributable disk image (.dmg) from the pkg.

    Args:
      pkg_filename: the name of the pkg file (which is technically
                    a directory).
      dmg_filename: the name of the dmg file.

    Returns:
      True if successful, False otherwise.
    """
    command = (
        u'hdiutil create {0:s} -srcfolder {1:s} -fs HFS+').format(
            dmg_filename, pkg_filename)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _BuildPkg(
      self, source_directory, project_identifier, project_version,
      pkg_filename):
    """Builds the distributable disk image (.dmg) from the pkg.

    Args:
      source_directory: the name of the source directory.
      project_identifier: the project identifier.
      project_version: the version of the project.
      pkg_filename: the name of the pkg file (which is technically
                    a directory).

    Returns:
      True if successful, False otherwise.
    """
    command = (
        u'{0:s} --root {1:s}/tmp/ --identifier {2:s} '
        u'--version {3!s} --ownership recommended {4:s}').format(
            self._pkgbuild, source_directory, project_identifier,
            project_version, pkg_filename)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def CheckBuildDependencies(self):
    """Checks if the build dependencies are met.

    Returns:
      A list of build dependency names that are not met or an empty list.
    """
    # TODO: implement build dependency check.
    return []

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if a build is required, False otherwise.
    """
    dmg_filename = u'{0:s}-{1!s}.dmg'.format(
        source_helper_object.project_name, source_helper_object.project_version)

    return not os.path.exists(dmg_filename)

  def Clean(self, source_helper_object):
    """Cleans the MacOS-X packages in the current directory.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).
    """
    filenames_to_ignore = re.compile(u'^{0:s}-.*{1!s}'.format(
        source_helper_object.project_name,
        source_helper_object.project_version))

    # Remove files of previous versions in the format:
    # project-*version.dmg
    filenames = glob.glob(u'{0:s}-*.dmg'.format(
        source_helper_object.project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # project-*version.pkg
    filenames = glob.glob(u'{0:s}-*.pkg'.format(
        source_helper_object.project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)


class ConfigureMakePkgBuildHelper(PkgBuildHelper):
  """Class that helps in building MacOS-X packages (.pkg)."""

  _DOC_FILENAMES = frozenset([
      u'AUTHORS',
      u'AUTHORS.txt',
      u'COPYING',
      u'COPYING.txt',
      u'LICENSE',
      u'LICENSE.txt',
      u'NEWS',
      u'NEWS.txt',
      u'README',
      u'README.md',
      u'README.txt'])

  def Build(self, source_helper_object):
    """Builds the pkg package and distributable disk image (.dmg).

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building pkg of: {0:s}'.format(source_filename))

    if self._dependency_definition.patches:
      # TODO: add self._ApplyPatches
      pass

    dmg_filename = u'{0:s}-{1!s}.dmg'.format(
        source_helper_object.project_name, source_helper_object.project_version)
    pkg_filename = u'{0:s}-{1!s}.pkg'.format(
        source_helper_object.project_name, source_helper_object.project_version)
    log_filename = os.path.join(u'..', self.LOG_FILENAME)

    sdks_path = os.path.join(
        u'/', u'Applications', u'Xcode.app', u'Contents', u'Developer',
        u'Platforms', u'MacOSX.platform', u'Developer', u'SDKs')

    for sdk_version in (u'10.7', u'10.8', '10.9', '10.10', '10.11'):
      sdk_sub_path = u'MacOSX{0:s}.sdk'.format(sdk_version)
      sdk_path = os.path.join(sdks_path, sdk_sub_path)
      if os.path.isdir(sdk_sub_path):
        break

    if sdk_path:
      cflags = u'CFLAGS="-isysroot {0:s}"'.format(sdk_path)
      ldflags = u'LDFLAGS="-Wl,-syslibroot,{0:s}"'.format(sdk_path)
    else:
      cflags = u''
      ldflags = u''

    if not os.path.exists(pkg_filename):
      prefix = u'/usr/local'
      configure_options = u''
      if self._dependency_definition.pkg_configure_options:
        configure_options = u' '.join(
            self._dependency_definition.pkg_configure_options)

      elif self._dependency_definition.configure_options:
        configure_options = u' '.join(
            self._dependency_definition.configure_options)

      if cflags and ldflags:
        command = (
            u'{0:s} {1:s} ./configure --prefix={2:s} {3:s} '
            u'--disable-dependency-tracking > {4:s} 2>&1').format(
                cflags, ldflags, prefix, configure_options, log_filename)
      else:
        command = (
            u'./configure --prefix={0:s} {1:s} > {2:s} 2>&1').format(
                prefix, configure_options, log_filename)

      exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
          source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      command = u'make >> {0:s} 2>&1'.format(log_filename)
      exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
          source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      command = u'make install DESTDIR={0:s}/tmp >> {1:s} 2>&1'.format(
          os.path.abspath(source_directory), log_filename)
      exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
          source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      share_doc_path = os.path.join(
          source_directory, u'tmp', u'usr', u'local', u'share', u'doc',
          source_helper_object.project_name)
      if not os.path.exists(share_doc_path):
        os.makedirs(share_doc_path)

      for doc_filename in self._DOC_FILENAMES:
        doc_path = os.path.join(source_directory, doc_filename)
        if os.path.exists(doc_path):
          shutil.copy(doc_path, share_doc_path)

      licenses_directory = os.path.join(source_directory, u'licenses')
      if os.path.isdir(licenses_directory):
        for doc_path in glob.glob(os.path.join(licenses_directory, u'*')):
          shutil.copy(doc_path, share_doc_path)

      project_identifier = u'com.github.libyal.{0:s}'.format(
          source_helper_object.project_name)
      if not self._BuildPkg(
          source_directory, project_identifier,
          source_helper_object.project_version, pkg_filename):
        return False

    if not self._BuildDmg(pkg_filename, dmg_filename):
      return False

    return True


class SetupPyPkgBuildHelper(PkgBuildHelper):
  """Class that helps in building MacOS-X packages (.pkg)."""

  def Build(self, source_helper_object):
    """Builds the pkg package and distributable disk image (.dmg).

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building pkg of: {0:s}'.format(source_filename))

    if self._dependency_definition.patches:
      # TODO: add self._ApplyPatches
      pass

    dmg_filename = u'{0:s}-{1!s}.dmg'.format(
        source_helper_object.project_name, source_helper_object.project_version)
    pkg_filename = u'{0:s}-{1!s}.pkg'.format(
        source_helper_object.project_name, source_helper_object.project_version)
    log_filename = os.path.join(u'..', self.LOG_FILENAME)

    if not os.path.exists(pkg_filename):
      command = u'python setup.py build > {0:s} 2>&1'.format(log_filename)
      exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
          source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      command = (
          u'python setup.py install --root={0:s}/tmp '
          u'--install-data=/usr/local > {1:s} 2>&1').format(
              os.path.abspath(source_directory), log_filename)
      exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
          source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      # Copy the license file to the egg-info sub directory.
      for license_file in [
          u'COPYING', u'LICENSE', u'LICENSE.TXT', u'LICENSE.txt']:
        if not os.path.exists(os.path.join(source_directory, license_file)):
          continue

        command = (
            u'find ./tmp -type d -name \\*.egg-info -exec cp {0:s} {{}} '
            u'\\;').format(license_file)
        exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
            source_directory, command), shell=True)
        if exit_code != 0:
          logging.error(u'Running: "{0:s}" failed.'.format(command))
          return False

      project_identifier = source_helper_object.GetProjectIdentifier()
      if not self._BuildPkg(
          source_directory, project_identifier,
          source_helper_object.project_version, pkg_filename):
        return False

    if not self._BuildDmg(pkg_filename, dmg_filename):
      return False

    return True


class RpmBuildHelper(BuildHelper):
  """Class that helps in building rpm packages (.rpm)."""

  _BUILD_DEPENDENCIES = frozenset([
      u'git',
      u'binutils',
      u'autoconf',
      u'automake',
      u'libtool',
      u'gettext-devel',
      u'make',
      u'pkgconfig',
      u'gcc',
      u'gcc-c++',
      u'flex',
      u'byacc',
      u'rpm-build',
      u'python-devel',
      u'python-dateutil',
      u'python-setuptools',
      u'python-test'
  ])

  _BUILD_DEPENDENCY_PACKAGE_NAMES = {
      u'bzip2': u'bzip2-devel',
      u'fuse': u'fuse-devel',
      u'libcrypto': u'openssl-devel',
      u'sqlite': u'sqlite-devel',
      u'zeromq': u'libzmq3-devel',
      u'zlib': u'zlib-devel'
  }

  def __init__(self, dependency_definition, l2tdevtools_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      l2tdevtools_path: the path to the l2tdevtools directory.
    """
    super(RpmBuildHelper, self).__init__(
        dependency_definition, l2tdevtools_path)
    self.architecture = platform.machine()

    self.rpmbuild_path = os.path.join(u'~', u'rpmbuild')
    self.rpmbuild_path = os.path.expanduser(self.rpmbuild_path)

    self._rpmbuild_rpms_path = os.path.join(
        self.rpmbuild_path, u'RPMS', self.architecture)
    self._rpmbuild_sources_path = os.path.join(self.rpmbuild_path, u'SOURCES')
    self._rpmbuild_specs_path = os.path.join(self.rpmbuild_path, u'SPECS')

  def _BuildFromSpecFile(self, spec_filename):
    """Builds the rpms directly from a spec file.

    Args:
      spec_filename: the name of the spec file as stored in the rpmbuild
                     SPECS sub directory.

    Returns:
      True if successful, False otherwise.
    """
    current_path = os.getcwd()
    os.chdir(self.rpmbuild_path)

    command = u'rpmbuild -ba {0:s} > {1:s} 2>&1'.format(
        os.path.join(u'SPECS', spec_filename), self.LOG_FILENAME)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))

    os.chdir(current_path)

    return exit_code == 0

  def _BuildFromSourcePackage(self, source_filename):
    """Builds the rpms directly from the source package file.

    For this to work the source package needs to contain a valid rpm .spec file.

    Args:
      source_filename: the name of the source package file.

    Returns:
      True if successful, False otherwise.
    """
    command = u'rpmbuild -ta {0:s} > {1:s} 2>&1'.format(
        source_filename, self.LOG_FILENAME)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _CheckIsInstalled(self, package_name):
    """Checks if a package is installed.

    Args:
      package_name: the name of the package.

    Returns:
      A boolean value containing true if the package is installed
      false otherwise.
    """
    command = u'rpm -qi {0:s} >/dev/null 2>&1'.format(package_name)
    exit_code = subprocess.call(command, shell=True)
    return exit_code == 0

  def _CreateRpmbuildDirectories(self):
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
      project_name: the name of the project.
      spec_file_data: the spec file data.
    """
    spec_filename = os.path.join(
        self._rpmbuild_specs_path, u'{0:s}.spec'.format(project_name))

    spec_file = open(spec_filename, 'w')
    spec_file.write(spec_file_data)
    spec_file.close()

  def _CopySourceFile(self, source_filename):
    """Copies the source file to the rpmbuild directory.

    Args:
      source_filename: the name of the source package file.
    """
    shutil.copy(source_filename, self._rpmbuild_sources_path)

  def _GetFilenameSafeProjectInformation(self, source_helper_object):
    """Determines the filename safe project name and version.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      A tuple containing the filename safe project name and version.
    """
    if self._dependency_definition.setup_name:
      project_name = self._dependency_definition.setup_name
    else:
      project_name = source_helper_object.project_name

    project_version = source_helper_object.project_version
    if isinstance(project_version, basestring):
      project_version = project_version.replace(u'-', u'_')

    return project_name, project_version

  def _MoveRpms(self, project_name, project_version):
    """Moves the rpms from the rpmbuild directory into the current directory.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.
    """
    filenames = glob.glob(os.path.join(
        self._rpmbuild_rpms_path, u'{0:s}-*{1!s}-1.{2:s}.rpm'.format(
            project_name, project_version, self.architecture)))
    for filename in filenames:
      logging.info(u'Moving: {0:s}'.format(filename))
      shutil.move(filename, u'.')

  def CheckBuildDependencies(self):
    """Checks if the build dependencies are met.

    Returns:
      A list of build dependency names that are not met or an empty list.
    """
    missing_packages = []
    for package_name in self._BUILD_DEPENDENCIES:
      if not self._CheckIsInstalled(package_name):
        missing_packages.append(package_name)

    for package_name in self._dependency_definition.build_dependencies:
      package_name = self._BUILD_DEPENDENCY_PACKAGE_NAMES.get(
          package_name, package_name)
      if not self._CheckIsInstalled(package_name):
        missing_packages.append(package_name)

    return missing_packages

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if a build is required, False otherwise.
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    rpm_filename = u'{0:s}-{1!s}-1.{2:s}.rpm'.format(
        project_name, project_version, self.architecture)

    return not os.path.exists(rpm_filename)

  def Clean(self, source_helper_object):
    """Cleans the rpmbuild directory.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).
    """
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    # Remove previous versions build directories.
    filenames_to_ignore = re.compile(u'{0:s}-{1!s}'.format(
        project_name, project_version))

    filenames = glob.glob(os.path.join(
        self.rpmbuild_path, u'BUILD', u'{0:s}-*'.format(project_name)))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        shutil.rmtree(filename)

    # Remove previous versions of rpms.
    filenames_to_ignore = re.compile(
        u'{0:s}-.*{1!s}-1.{2:s}.rpm'.format(
            project_name, project_version, self.architecture))

    rpm_filenames_glob = u'{0:s}-*-1.{1:s}.rpm'.format(
        project_name, self.architecture)

    filenames = glob.glob(rpm_filenames_glob)
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames = glob.glob(os.path.join(
        self.rpmbuild_path, u'RPMS', self.architecture, rpm_filenames_glob))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove previous versions of source rpms.
    filenames_to_ignore = re.compile(u'{0:s}-.*{1!s}-1.src.rpm'.format(
        project_name, project_version))

    filenames = glob.glob(os.path.join(
        self.rpmbuild_path, u'SRPMS',
        u'{0:s}-*-1.src.rpm'.format(project_name)))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)


class ConfigureMakeRpmBuildHelper(RpmBuildHelper):
  """Class that helps in building rpm packages (.rpm)."""

  def Build(self, source_helper_object):
    """Builds the rpms.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    logging.info(u'Building rpm of: {0:s}'.format(source_filename))

    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    # rpmbuild wants the project filename without the status indication.
    rpm_source_filename = u'{0:s}-{1!s}.tar.gz'.format(
        project_name, project_version)
    os.rename(source_filename, rpm_source_filename)

    build_successful = self._BuildFromSourcePackage(rpm_source_filename)

    if build_successful:
      self._MoveRpms(project_name, project_version)

      # Remove BUILD directory.
      filename = os.path.join(
          self.rpmbuild_path, u'BUILD', u'{0:s}-{1!s}'.format(
              project_name, project_version))
      logging.info(u'Removing: {0:s}'.format(filename))
      shutil.rmtree(filename)

      # Remove SRPMS file.
      filename = os.path.join(
          self.rpmbuild_path, u'SRPMS', u'{0:s}-{1!s}-1.src.rpm'.format(
              project_name, project_version))
      logging.info(u'Removing: {0:s}'.format(filename))
      os.remove(filename)

    # Change the project filename back to the original.
    os.rename(rpm_source_filename, source_filename)

    return build_successful


class SetupPyRpmBuildHelper(RpmBuildHelper):
  """Class that helps in building rpm packages (.rpm)."""

  def __init__(self, dependency_definition, l2tdevtools_path):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      l2tdevtools_path: the path to the l2tdevtools directory.
    """
    super(SetupPyRpmBuildHelper, self).__init__(
        dependency_definition, l2tdevtools_path)
    if not dependency_definition.architecture_dependent:
      self.architecture = u'noarch'

  def Build(self, source_helper_object):
    """Builds the rpms.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    logging.info(u'Building rpm of: {0:s}'.format(source_filename))

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    command = u'python setup.py bdist_rpm > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    # Move the rpms to the build directory.
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    filenames = glob.glob(os.path.join(
        source_directory, u'dist', u'{0:s}-{1!s}-1.{2:s}.rpm'.format(
            project_name, project_version, self.architecture)))
    for filename in filenames:
      logging.info(u'Moving: {0:s}'.format(filename))
      shutil.move(filename, u'.')

    return True

  def Clean(self, source_helper_object):
    """Cleans the build and dist directory.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).
    """
    # Remove previous versions build directories.
    for filename in [u'build', u'dist']:
      if os.path.exists(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        shutil.rmtree(filename, True)

    # Remove previous versions of rpms.
    project_name, project_version = self._GetFilenameSafeProjectInformation(
        source_helper_object)

    filenames_to_ignore = re.compile(u'{0:s}-.*{1!s}-1.{2:s}.rpm'.format(
        project_name, project_version, self.architecture))

    rpm_filenames_glob = u'{0:s}-*-1.{1:s}.rpm'.format(
        project_name, self.architecture)

    filenames = glob.glob(rpm_filenames_glob)
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)


class SourceBuildHelper(BuildHelper):
  """Class that helps in building source."""


class ConfigureMakeSourceBuildHelper(SourceBuildHelper):
  """Class that helps in building source."""

  def Build(self, source_helper_object):
    """Builds the source.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building source of: {0:s}'.format(source_filename))

    if self._dependency_definition.patches:
      # TODO: add self._ApplyPatches
      pass

    log_filename = os.path.join(u'..', self.LOG_FILENAME)

    command = u'./configure > {0:s} 2>&1'.format(log_filename)
    exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    command = u'make >> {0:s} 2>&1'.format(log_filename)
    exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def Clean(self, unused_source_helper_object):
    """Cleans the source.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).
    """
    # TODO: implement.
    return


class SetupPySourceBuildHelper(SourceBuildHelper):
  """Class that helps in building source."""

  def Build(self, source_helper_object):
    """Builds the source.

    Args:
      source_helper_object: the source helper object (instance of SourceHelper).

    Returns:
      True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info(u'Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    logging.info(u'Building source of: {0:s}'.format(source_filename))

    if self._dependency_definition.patches:
      # TODO: add self._ApplyPatches
      pass

    command = u'{0:s} setup.py build > {1:s} 2>&1'.format(
        sys.executable, os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(u'(cd {0:s} && {1:s})'.format(
        source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True


class BuildHelperFactory(object):
  """Factory class for build helpers."""

  _CONFIGURE_MAKE_BUILD_HELPER_CLASSES = {
      u'dpkg': ConfigureMakeDpkgBuildHelper,
      u'dpkg-source': ConfigureMakeSourceDpkgBuildHelper,
      u'msi': ConfigureMakeMsiBuildHelper,
      u'osc': ConfigureMakeOscBuildHelper,
      u'pkg': ConfigureMakePkgBuildHelper,
      u'rpm': ConfigureMakeRpmBuildHelper,
      u'source': ConfigureMakeSourceBuildHelper,
  }

  _SETUP_PY_BUILD_HELPER_CLASSES = {
      u'dpkg': SetupPyDpkgBuildHelper,
      u'dpkg-source': SetupPySourceDpkgBuildHelper,
      u'msi': SetupPyMsiBuildHelper,
      u'osc': SetupPyOscBuildHelper,
      u'pkg': SetupPyPkgBuildHelper,
      u'rpm': SetupPyRpmBuildHelper,
      u'source': SetupPySourceBuildHelper,
  }

  @classmethod
  def NewBuildHelper(
      cls, dependency_definition, build_target, l2tdevtools_path):
    """Creates a new build helper object.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
      build_target: a string containing the build target.
      l2tdevtools_path: the path to the l2tdevtools directory.

    Returns:
      A build helper object (instance of BuildHelper) or None.
    """
    if dependency_definition.build_system == u'configure_make':
      build_helper_class = cls._CONFIGURE_MAKE_BUILD_HELPER_CLASSES.get(
          build_target, None)

    elif dependency_definition.build_system == u'setup_py':
      build_helper_class = cls._SETUP_PY_BUILD_HELPER_CLASSES.get(
          build_target, None)

    else:
      build_helper_class = None

    if not build_helper_class:
      return

    return build_helper_class(dependency_definition, l2tdevtools_path)
