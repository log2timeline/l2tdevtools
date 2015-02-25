# -*- coding: utf-8 -*-
"""Build helper object implementations."""

import fileinput
import glob
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import time


class BuildHelper(object):
  """Base class that helps in building."""

  LOG_FILENAME = u'build.log'

  def __init__(self, dependency_definition):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
    """
    super(BuildHelper, self).__init__()
    self._dependency_definition = dependency_definition


class DpkgBuildHelper(BuildHelper):
  """Class that helps in building dpkg packages (.deb)."""

  # TODO: determine BUILD_DEPENDENCIES from the build files?
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
      u'fakeroot',
      u'quilt',
      u'zlib1g-dev',
      u'libbz2-dev',
      u'libssl-dev',
      u'libfuse-dev',
      u'python-dev',
      u'python-setuptools',
      u'libsqlite3-dev',
  ])

  def _BuildPrepare(
      self, source_directory, project_name, project_version, version_suffix,
      distribution, architecture):
    """Make the necassary preperations before building the dpkg packages.

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
    if os.path.exists(u'prep-dpkg.sh'):
      command = u'sh ../prep-dpkg.sh {0:s} {1!s} {2:s} {3:s} {4:s}'.format(
          project_name, project_version, version_suffix, distribution,
          architecture)
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

    return True

  def _BuildFinalize(
      self, source_directory, project_name, project_version, version_suffix,
      distribution, architecture):
    """Make the necassary finalizations after building the dpkg packages.

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
    if os.path.exists(u'post-dpkg.sh'):
      command = u'sh ../post-dpkg.sh {0:s} {1!s} {2:s} {3:s} {4:s}'.format(
          project_name, project_version, version_suffix, distribution,
          architecture)
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

    return True

  @classmethod
  def CheckBuildDependencies(cls):
    """Checks if the build dependencies are met.

    Returns:
      A list of package names that need to be installed or an empty list.
    """
    missing_packages = []
    for package_name in cls._BUILD_DEPENDENCIES:
      if not cls.CheckIsInstalled(package_name):
        missing_packages.append(package_name)

    return missing_packages

  @classmethod
  def CheckIsInstalled(cls, package_name):
    """Checks if a package is installed.

    Args:
      package_name: the name of the package.

    Returns:
      A boolean value containing true if the package is installed
      false otherwise.
    """
    command = u'dpkg-query -l {0:s} >/dev/null 2>&1'.format(package_name)
    exit_code = subprocess.call(command, shell=True)
    return exit_code == 0


class LibyalDpkgBuildHelper(DpkgBuildHelper):
  """Class that helps in building libyal dpkg packages (.deb)."""

  def __init__(self, dependency_definition):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
    """
    super(LibyalDpkgBuildHelper, self).__init__(dependency_definition)
    self.architecture = platform.machine()
    self.distribution = u''
    self.version_suffix = u''

    if self.architecture == u'i686':
      self.architecture = u'i386'
    elif self.architecture == u'x86_64':
      self.architecture = u'amd64'

  def Build(self, source_helper):
    """Builds the dpkg packages.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    logging.info(u'Building deb of: {0:s}'.format(source_filename))

    # dpkg-buildpackage wants an source package filename without
    # the status indication and orig indication.
    deb_orig_source_filename = u'{0:s}_{1!s}.orig.tar.gz'.format(
        source_helper.project_name, source_helper.project_version)
    shutil.copy(source_filename, deb_orig_source_filename)

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    dpkg_directory = os.path.join(source_directory, u'dpkg')
    if not os.path.exists(dpkg_directory):
      dpkg_directory = os.path.join(source_directory, u'config', u'dpkg')

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
        source_directory, source_helper.project_name,
        source_helper.project_version, self.version_suffix, self.distribution,
        self.architecture):
      return False

    command = u'dpkg-buildpackage -uc -us -rfakeroot > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(
        u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    if not self._BuildFinalize(
        source_directory, source_helper.project_name,
        source_helper.project_version, self.version_suffix, self.distribution,
        self.architecture):
      return False

    return True

  def Clean(self, source_helper):
    """Cleans the dpkg packages in the current directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    filenames_to_ignore = re.compile(u'^{0:s}_{1!s}.orig.tar.gz'.format(
        source_helper.project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # project_version.orig.tar.gz
    filenames = glob.glob(
        u'{0:s}_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].orig.tar.gz'.format(
            source_helper.project_name, self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_to_ignore = re.compile(u'^{0:s}[-_].*{1!s}'.format(
        source_helper.project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # project[-_]version-1_architecture.*
    filenames = glob.glob(
        u'{0:s}[-_]*[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-1_'
        u'{1:s}.*'.format(source_helper.project_name, self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # project[-_]*version-1.*
    filenames = glob.glob(
        u'{0:s}[-_]*[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-1.*'.format(
            source_helper.project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, source_helper):
    """Retrieves the filename of one of the resulting files.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A filename of one of the resulting dpkg packages.
    """
    return u'{0:s}_{1!s}-1_{2:s}.deb'.format(
        source_helper.project_name, source_helper.project_version,
        self.architecture)


class LibyalSourceDpkgBuildHelper(DpkgBuildHelper):
  """Class that helps in building libyal source dpkg packages (.deb)."""

  def __init__(self, dependency_definition):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
    """
    super(LibyalSourceDpkgBuildHelper, self).__init__(dependency_definition)
    self.architecture = u'source'
    self.distribution = u'trusty'
    self.version_suffix = u'ppa1'

  def Build(self, source_helper):
    """Builds the dpkg packages.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    logging.info(u'Building source deb of: {0:s}'.format(source_filename))

    # dpkg-buildpackage wants an source package filename without
    # the status indication and orig indication.
    deb_orig_source_filename = u'{0:s}_{1!s}.orig.tar.gz'.format(
        source_helper.project_name, source_helper.project_version)
    shutil.copy(source_filename, deb_orig_source_filename)

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    dpkg_directory = os.path.join(source_directory, u'dpkg')
    if not os.path.exists(dpkg_directory):
      dpkg_directory = os.path.join(source_directory, u'config', u'dpkg')

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
        source_directory, source_helper.project_name,
        source_helper.project_version, self.version_suffix, self.distribution,
        self.architecture):
      return False

    command = u'debuild -S -sa > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(
        u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    if not self._BuildFinalize(
        source_directory, source_helper.project_name,
        source_helper.project_version, self.version_suffix, self.distribution,
        self.architecture):
      return False

    return True

  def Clean(self, source_helper):
    """Cleans the dpkg packages in the current directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    filenames_to_ignore = re.compile(u'^{0:s}_{1!s}.orig.tar.gz'.format(
        source_helper.project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # project_version.orig.tar.gz
    filenames = glob.glob(
        u'{0:s}_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].orig.tar.gz'.format(
            source_helper.project_name, self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_to_ignore = re.compile(u'^{0:s}[-_].*{1!s}'.format(
        source_helper.project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # project[-_]version-1suffix~distribution_architecture.*
    filenames = glob.glob((
        u'{0:s}[-_]*[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'
        u'-1{1:s}~{2:s}_{3:s}.*').format(
            source_helper.project_name, self.version_suffix, self.distribution,
            self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # project[-_]*version-1suffix~distribution.*
    filenames = glob.glob((
        u'{0:s}[-_]*[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'
        u'-1{1:s}~{2:s}.*').format(
            source_helper.project_name, self.version_suffix, self.distribution))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, source_helper):
    """Retrieves the filename of one of the resulting files.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A filename of one of the resulting dpkg packages.
    """
    return u'{0:s}_{1!s}-1{2:s}~{3:s}_{4:s}.changes'.format(
        source_helper.project_name, source_helper.project_version,
        self.version_suffix, self.distribution, self.architecture)


class PythonModuleDpkgBuildFilesGenerator(object):
  """Class that helps in generating dpkg build files for Python modules."""

  _EMAIL_ADDRESS = u'Log2Timeline <log2timeline-dev@googlegroups.com>'

  _DOCS_FILENAMES = [
      u'CHANGES', u'CHANGES.txt', u'CHANGES.TXT',
      u'LICENSE', u'LICENSE.txt', u'LICENSE.TXT',
      u'README', u'README.txt', u'README.TXT']

  _CHANGELOG_TEMPLATE = u'\n'.join([
      u'python-{project_name:s} ({project_version!s}-1) unstable; urgency=low',
      u'',
      u'  * Auto-generated',
      u'',
      u' -- {maintainer_email_address:s}  {date_time:s}'])

  _COMPAT_TEMPLATE = u'\n'.join([
      u'7'])

  _CONTROL_TEMPLATE = u'\n'.join([
      u'Source: python-{project_name:s}',
      u'Section: python',
      u'Priority: extra',
      u'Maintainer: {upstream_maintainer:s}',
      u'Build-Depends: debhelper (>= 7), python, python-setuptools',
      u'Standards-Version: 3.9.5',
      u'Homepage: {upstream_homepage:s}',
      u'',
      u'Package: python-{project_name:s}',
      u'Architecture: all',
      u'Depends: {depends:s}',
      u'Description: {description_short:s}',
      u' {description_long:s}',
      u''])

  _COPYRIGHT_TEMPLATE = u'\n'.join([
      u''])

  _RULES_TEMPLATE = u'\n'.join([
      u'#!/usr/bin/make -f',
      u'# debian/rules that uses debhelper >= 7.',
      u'',
      u'# Uncomment this to turn on verbose mode.',
      u'#export DH_VERBOSE=1',
      u'',
      u'# This has to be exported to make some magic below work.',
      u'export DH_OPTIONS',
      u'',
      u'',
      u'%:',
      u'	dh  $@ --with python2',
      u'',
      u'.PHONY: override_dh_auto_test',
      u'override_dh_auto_test:',
      u'',
      u'.PHONY: override_dh_installmenu',
      u'override_dh_installmenu:',
      u'',
      u'.PHONY: override_dh_installmime',
      u'override_dh_installmime:',
      u'',
      u'.PHONY: override_dh_installmodules',
      u'override_dh_installmodules:',
      u'',
      u'.PHONY: override_dh_installlogcheck',
      u'override_dh_installlogcheck:',
      u'',
      u'.PHONY: override_dh_installlogrotate',
      u'override_dh_installlogrotate:',
      u'',
      u'.PHONY: override_dh_installpam',
      u'override_dh_installpam:',
      u'',
      u'.PHONY: override_dh_installppp',
      u'override_dh_installppp:',
      u'',
      u'.PHONY: override_dh_installudev',
      u'override_dh_installudev:',
      u'',
      u'.PHONY: override_dh_installwm',
      u'override_dh_installwm:',
      u'',
      u'.PHONY: override_dh_installxfonts',
      u'override_dh_installxfonts:',
      u'',
      u'.PHONY: override_dh_gconf',
      u'override_dh_gconf:',
      u'',
      u'.PHONY: override_dh_icons',
      u'override_dh_icons:',
      u'',
      u'.PHONY: override_dh_perl',
      u'override_dh_perl:',
      u'',
      u'.PHONY: override_dh_pysupport',
      u'override_dh_pysupport:',
      u'',
      u'.PHONY: override_dh_python2',
      u'override_dh_python2:',
      u'	dh_python2 -V 2.7 setup.py',
      u''])

  _SOURCE_FORMAT_TEMPLATE = u'\n'.join([
      u'1.0'])

  def __init__(
      self, project_name, project_version, dependency_definition):
    """Initializes the dpkg build files generator.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
    """
    super(PythonModuleDpkgBuildFilesGenerator, self).__init__()
    self._project_name = project_name
    self._project_version = project_version
    self._dependency_definition = dependency_definition

  def _GenerateChangelogFile(self, dpkg_path):
    """Generate the dpkg build changelog file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    timezone_minutes, _ = divmod(time.timezone, 60)
    timezone_hours, timezone_minutes = divmod(timezone_minutes, 60)

    # If timezone_hours is -1 {0:02d} will format as -1 instead of -01
    # hence we detect the sign and force a leading zero.
    if timezone_hours < 0:
      timezone_string = u'-{0:02d}{1:02d}'.format(
          -timezone_hours, timezone_minutes)
    else:
      timezone_string = u'+{0:02d}{1:02d}'.format(
          timezone_hours, timezone_minutes)

    date_time_string = u'{0:s} {1:s}'.format(
        time.strftime('%a, %d %b %Y %H:%M:%S'), timezone_string)

    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = self._project_name

    template_values = {
        'project_name': project_name,
        'project_version': self._project_version,
        'maintainer_email_address': self._EMAIL_ADDRESS,
        'date_time': date_time_string}

    filename = os.path.join(dpkg_path, u'changelog')
    with open(filename, 'wb') as file_object:
      data = self._CHANGELOG_TEMPLATE.format(**template_values)
      file_object.write(data.encode('utf-8'))

  def _GenerateCompatFile(self, dpkg_path):
    """Generate the dpkg build compat file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    filename = os.path.join(dpkg_path, u'compat')
    with open(filename, 'wb') as file_object:
      data = self._COMPAT_TEMPLATE
      file_object.write(data.encode('utf-8'))

  def _GenerateControlFile(self, dpkg_path):
    """Generate the dpkg build control file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = self._project_name

    depends = []
    if self._dependency_definition.dpkg_dependencies:
      depends.append(self._dependency_definition.dpkg_dependencies)
    depends.append('${shlibs:Depends}')
    depends.append('${misc:Depends}')
    depends = u', '.join(depends)

    # description short needs to be a single line.
    description_short = self._dependency_definition.description_short
    description_short = u' '.join(description_short.split(u'\n'))

    # description long needs a space at the start of every line after
    # the first.
    description_long = self._dependency_definition.description_long
    description_long = u'\n '.join(description_long.split(u'\n'))

    template_values = {
        'project_name': project_name,
        'upstream_maintainer': self._dependency_definition.maintainer,
        'upstream_homepage': self._dependency_definition.homepage_url,
        'depends': depends,
        'description_short': description_short,
        'description_long': description_long}

    filename = os.path.join(dpkg_path, u'control')
    with open(filename, 'wb') as file_object:
      data = self._CONTROL_TEMPLATE.format(**template_values)
      file_object.write(data.encode('utf-8'))

  def _GenerateCopyrightFile(self, dpkg_path):
    """Generate the dpkg build copyright file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    license_file = os.path.dirname(__file__)
    license_file = os.path.dirname(license_file)
    license_file = os.path.join(
        license_file, u'data', u'licenses', u'LICENSE.{0:s}'.format(
            self._project_name))

    filename = os.path.join(dpkg_path, u'copyright')

    shutil.copy(license_file, filename)

  def _GenerateDocsFile(self, dpkg_path):
    """Generate the dpkg build .docs file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = self._project_name

    # Determine the available doc files.
    doc_files = []
    for filename in self._DOCS_FILENAMES:
      if os.path.exists(filename):
        doc_files.append(filename)

    filename = os.path.join(
        dpkg_path, u'python-{0:s}.docs'.format(project_name))
    with open(filename, 'wb') as file_object:
      file_object.write(u'\n'.join(doc_files))

  def _GenerateRulesFile(self, dpkg_path):
    """Generate the dpkg build rules file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    filename = os.path.join(dpkg_path, u'rules')
    with open(filename, 'wb') as file_object:
      data = self._RULES_TEMPLATE
      file_object.write(data.encode('utf-8'))

  def _GenerateSourceFormatFile(self, dpkg_path):
    """Generate the dpkg build source/format file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    filename = os.path.join(dpkg_path, u'source', u'format')
    with open(filename, 'wb') as file_object:
      data = self._SOURCE_FORMAT_TEMPLATE
      file_object.write(data.encode('utf-8'))

  def GenerateFiles(self, dpkg_path):
    """Generate the dpkg build files.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    os.mkdir(dpkg_path)
    self._GenerateChangelogFile(dpkg_path)
    self._GenerateCompatFile(dpkg_path)
    self._GenerateControlFile(dpkg_path)
    self._GenerateCopyrightFile(dpkg_path)
    self._GenerateDocsFile(dpkg_path)
    self._GenerateRulesFile(dpkg_path)

    os.mkdir(os.path.join(dpkg_path, u'source'))
    self._GenerateSourceFormatFile(dpkg_path)


class PythonModuleDpkgBuildHelper(DpkgBuildHelper):
  """Class that helps in building python module dpkg packages (.deb)."""

  def __init__(self, dependency_definition):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
    """
    super(PythonModuleDpkgBuildHelper, self).__init__(dependency_definition)
    self.architecture = u'all'
    self.distribution = u''
    self.version_suffix = u''

  def Build(self, source_helper):
    """Builds the dpkg packages.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    logging.info(u'Building deb of: {0:s}'.format(source_filename))

    # dpkg-buildpackage wants an source package filename without
    # the status indication and orig indication.
    deb_orig_source_filename = u'python-{0:s}_{1!s}.orig.tar.gz'.format(
        source_helper.project_name, source_helper.project_version)
    shutil.copy(source_filename, deb_orig_source_filename)

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    dpkg_directory = os.path.join(source_directory, u'dpkg')
    if not os.path.exists(dpkg_directory):
      dpkg_directory = os.path.join(source_directory, u'config', u'dpkg')

    if not os.path.exists(dpkg_directory):
      # Generate the dpkg build files if necessary.
      os.chdir(source_directory)

      build_files_generator = PythonModuleDpkgBuildFilesGenerator(
          source_helper.project_name, source_helper.project_version,
          self._dependency_definition)
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
        source_directory, source_helper.project_name,
        source_helper.project_version, self.version_suffix, self.distribution,
        self.architecture):
      return False

    command = u'dpkg-buildpackage -uc -us -rfakeroot > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(
        u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    if not self._BuildFinalize(
        source_directory, source_helper.project_name,
        source_helper.project_version, self.version_suffix, self.distribution,
        self.architecture):
      return False

    return True

  def Clean(self, source_helper):
    """Cleans the dpkg packages in the current directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = source_helper.project_name

    filenames_to_ignore = re.compile(u'^python-{0:s}_{1!s}.orig.tar.gz'.format(
        project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # python-project_version.orig.tar.gz
    filenames = glob.glob(u'python-{0:s}_*.orig.tar.gz'.format(
        project_name, self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_to_ignore = re.compile(u'^python-{0:s}[-_].*{1!s}'.format(
        project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # python-project[-_]*version-1_architecture.*
    filenames = glob.glob(
        u'python-{0:s}[-_]*-1_{1:s}.*'.format(project_name, self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # python-project[-_]*version-1.*
    filenames = glob.glob(u'python-{0:s}[-_]*-1.*'.format(project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, source_helper):
    """Retrieves the filename of one of the resulting files.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A filename of one of the resulting dpkg packages.
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = source_helper.project_name

    return u'python-{0:s}_{1!s}-1_{2:s}.deb'.format(
        project_name, source_helper.project_version, self.architecture)


class PythonModuleSourceDpkgBuildHelper(DpkgBuildHelper):
  """Class that helps in building python module source dpkg packages (.deb)."""

  def __init__(self, dependency_definition):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
    """
    super(PythonModuleSourceDpkgBuildHelper, self).__init__(
        dependency_definition)
    self.architecture = u'source'
    self.distribution = u'trusty'
    self.version_suffix = u'ppa1'

  def Build(self, source_helper):
    """Builds the dpkg packages.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    logging.info(u'Building source deb of: {0:s}'.format(source_filename))

    # dpkg-buildpackage wants an source package filename without
    # the status indication and orig indication.
    deb_orig_source_filename = u'python-{0:s}_{1!s}.orig.tar.gz'.format(
        source_helper.project_name, source_helper.project_version)
    shutil.copy(source_filename, deb_orig_source_filename)

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    dpkg_directory = os.path.join(source_directory, u'dpkg')
    if not os.path.exists(dpkg_directory):
      dpkg_directory = os.path.join(source_directory, u'config', u'dpkg')

    if not os.path.exists(dpkg_directory):
      # Generate the dpkg build files if necessary.
      os.chdir(source_directory)

      build_files_generator = PythonModuleDpkgBuildFilesGenerator(
          source_helper.project_name, source_helper.project_version,
          self._dependency_definition)
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
        source_directory, source_helper.project_name,
        source_helper.project_version, self.version_suffix, self.distribution,
        self.architecture):
      return False

    command = u'debuild -S -sa > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(
        u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    if not self._BuildFinalize(
        source_directory, source_helper.project_name,
        source_helper.project_version, self.version_suffix, self.distribution,
        self.architecture):
      return False

    return True

  def Clean(self, source_helper):
    """Cleans the dpkg packages in the current directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = source_helper.project_name

    filenames_to_ignore = re.compile(u'^python-{0:s}_{1!s}.orig.tar.gz'.format(
        project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # python-project_version.orig.tar.gz
    filenames = glob.glob(u'python-{0:s}_*.orig.tar.gz'.format(
        project_name, self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames_to_ignore = re.compile(u'^python-{0:s}[-_].*{1!s}'.format(
        project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # python-project[-_]*version-1suffix~distribution_architecture.*
    filenames = glob.glob((
        u'python-{0:s}[-_]*-1{1:s}~{2:s}_{3:s}.*').format(
            project_name, self.version_suffix, self.distribution,
            self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # python-project[-_]*version-1suffix~distribution.*
    filenames = glob.glob((
        u'python-{0:s}[-_]*-1{1:s}~{2:s}.*').format(
            project_name, self.version_suffix, self.distribution))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, source_helper):
    """Retrieves the filename of one of the resulting files.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A filename of one of the resulting dpkg packages.
    """
    if self._dependency_definition.dpkg_name:
      project_name = self._dependency_definition.dpkg_name
    else:
      project_name = source_helper.project_name

    return u'python-{0:s}_{1!s}-1{2:s}~{3:s}_{4:s}.changes'.format(
        project_name, source_helper.project_version,
        self.version_suffix, self.distribution, self.architecture)


class MsiBuildHelper(BuildHelper):
  """Class that helps in building Microsoft Installer packages (.msi)."""

  def __init__(self, dependency_definition):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
    """
    super(MsiBuildHelper, self).__init__(dependency_definition)
    self.architecture = platform.machine()

    if self.architecture == u'x86':
      self.architecture = u'win32'
    elif self.architecture == u'AMD64':
      self.architecture = u'win-amd64'


class LibyalMsiBuildHelper(MsiBuildHelper):
  """Class that helps in building Microsoft Installer packages (.msi)."""

  def __init__(self, dependency_definition):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).

    Raises:
      RuntimeError: if the Visual Studio version could be determined or
                    msvscpp-convert.py could not be found.
    """
    super(LibyalMsiBuildHelper, self).__init__(dependency_definition)

    if 'VS90COMNTOOLS' in os.environ:
      self.version = '2008'

    elif 'VS100COMNTOOLS' in os.environ:
      self.version = '2010'

    elif 'VS110COMNTOOLS' in os.environ:
      self.version = '2012'

    elif 'VS120COMNTOOLS' in os.environ:
      self.version = '2013'

    else:
      raise RuntimeError(u'Unable to determine Visual Studio version.')

    if self.version != '2008':
      self._msvscpp_convert = os.path.join(
          os.path.dirname(__file__), u'msvscpp-convert.py')

      if not os.path.exists(self._msvscpp_convert):
        raise RuntimeError(u'Unable to find msvscpp-convert.py')

  def _BuildPrepare(self, source_directory):
    """Prepares the source for building with Visual Studio.

    Args:
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
          if self.version == '2008':
            if not line.startswith('#define WINVER 0x0501'):
              print '#define WINVER 0x0501'
              print ''

          else:
            if not line.startswith('#define WINVER 0x0600'):
              print '#define WINVER 0x0600'
              print ''

          parsing_mode = 2

        elif line.startswith('#define _CONFIG_'):
          parsing_mode = 1

      print line

  def _ConvertSolutionFiles(self, source_directory):
    """Converts the Visual Studio solution and project files.

    Args:
      source_directory: the name of the source directory.
    """
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

  def Build(self, source_helper):
    """Builds using Visual Studio.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    logging.info(u'Building: {0:s} with Visual Studio {1:s}'.format(
        source_filename, self.version))

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    # Search common locations for MSBuild.exe
    if self.version == '2008':
      msbuild = u'{0:s}:{1:s}{2:s}'.format(
          u'C', os.sep, os.path.join(
              u'Windows', u'Microsoft.NET', u'Framework', u'v3.5',
              u'MSBuild.exe'))

    # Note that MSBuild in .NET 3.5 does not support vs2010 solution files
    # and MSBuild in .NET 4.0 is needed instead.
    elif self.version in ['2010', '2012', '2013']:
      msbuild = u'{0:s}:{1:s}{2:s}'.format(
          u'C', os.sep, os.path.join(
              u'Windows', u'Microsoft.NET', u'Framework', u'v4.0.30319',
              u'MSBuild.exe'))

    if not os.path.exists(msbuild):
      logging.error(u'Unable to find MSBuild.exe')
      return False

    if self.version == '2008':
      if not os.environ['VS90COMNTOOLS']:
        logging.error(u'Missing VS90COMNTOOLS environment variable.')
        return False

    elif self.version == '2010':
      if not os.environ['VS100COMNTOOLS']:
        logging.error(u'Missing VS100COMNTOOLS environment variable.')
        return False

    elif self.version == '2012':
      if not os.environ['VS110COMNTOOLS']:
        logging.error(u'Missing VS110COMNTOOLS environment variable.')
        return False

    elif self.version == '2013':
      if not os.environ['VS120COMNTOOLS']:
        logging.error(u'Missing VS120COMNTOOLS environment variable.')
        return False

    # For the Visual Studio builds later than 2008 the convert the 2008
    # solution and project files need to be converted to the newer version.
    if self.version in ['2010', '2012', '2013']:
      self._ConvertSolutionFiles(source_directory)

    self._BuildPrepare(source_directory)

    # Detect architecture based on Visual Studion Platform environment
    # variable. If not set the platform with default to Win32.
    msvscpp_platform = os.environ.get('Platform', None)
    if not msvscpp_platform:
      msvscpp_platform = os.environ.get('TARGET_CPU', None)

    if not msvscpp_platform or msvscpp_platform == 'x86':
      msvscpp_platform = 'Win32'

    if msvscpp_platform not in ['Win32', 'x64']:
      logging.error(u'Unsupported build platform: {0:s}'.format(
          msvscpp_platform))
      return False

    if self.version == '2008' and msvscpp_platform == 'x64':
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

    if not os.path.exists(python_module_dist_directory):
      build_directory = os.path.join(u'..', u'..')

      os.chdir(python_module_directory)

      # Setup.py uses VS90COMNTOOLS which is vs2008 specific
      # so we need to set it for the other Visual Studio versions.
      if self.version == '2010':
        os.environ['VS90COMNTOOLS'] = os.environ['VS100COMNTOOLS']

      elif self.version == '2012':
        os.environ['VS90COMNTOOLS'] = os.environ['VS110COMNTOOLS']

      elif self.version == '2013':
        os.environ['VS90COMNTOOLS'] = os.environ['VS120COMNTOOLS']

      command = u'{0:s} setup.py bdist_msi'.format(sys.executable)
      exit_code = subprocess.call(command, shell=False)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      # Move the msi to the build directory.
      msi_filename = glob.glob(os.path.join(
          u'dist', u'{0:s}-*.msi'.format(python_module_name)))

      logging.info(u'Moving: {0:s}'.format(msi_filename[0]))
      shutil.move(msi_filename[0], build_directory)

      os.chdir(build_directory)

    return True

  def Clean(self, source_helper):
    """Cleans the build and dist directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    # Remove previous versions of msis.
    filenames_to_ignore = re.compile(u'{0:s}-.*{1!s}.1.{2:s}-py2.7.msi'.format(
        source_helper.project_name, source_helper.project_version,
        self.architecture))

    msi_filenames_glob = u'{0:s}-*.1.{1:s}-py2.7.msi'.format(
        source_helper.project_name, self.architecture)

    filenames = glob.glob(msi_filenames_glob)
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, source_helper):
    """Retrieves the filename of one of the resulting files.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A filename of one of the resulting msis.
    """
    return u'{0:s}-{1!s}.1.{2:s}-py2.7.msi'.format(
        source_helper.project_name, source_helper.project_version,
        self.architecture)


class PythonModuleMsiBuildHelper(MsiBuildHelper):
  """Class that helps in building Microsoft Installer packages (.msi)."""

  def Build(self, source_helper):
    """Builds the msi.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    logging.info(u'Building msi of: {0:s}'.format(source_filename))

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    command = u'{0:s} setup.py bdist_msi > {1:s} 2>&1'.format(
        sys.executable, os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(
        u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    # Move the msi to the build directory.
    msi_filename = glob.glob(os.path.join(
        source_directory, u'dist', u'{0:s}-*.msi'.format(
            source_helper.project_name)))

    logging.info(u'Moving: {0:s}'.format(msi_filename[0]))
    shutil.move(msi_filename[0], '.')

    return True

  def Clean(self, source_helper):
    """Cleans the build and dist directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    # Remove previous versions build directories.
    for filename in [u'build', u'dist']:
      if os.path.exists(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        shutil.rmtree(filename, True)

    # Remove previous versions of msis.
    filenames_to_ignore = re.compile(u'{0:s}-.*{1!s}.{2:s}.msi'.format(
        source_helper.project_name, source_helper.project_version,
        self.architecture))

    msi_filenames_glob = u'{0:s}-*.{1:s}.msi'.format(
        source_helper.project_name, self.architecture)

    filenames = glob.glob(msi_filenames_glob)
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, source_helper):
    """Retrieves the filename of one of the resulting files.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A filename of one of the resulting msis.
    """
    # TODO: this does not work for dfvfs at the moment. Fix this.
    return u'{0:s}-{1!s}.{2:s}.msi'.format(
        source_helper.project_name, source_helper.project_version,
        self.architecture)


class PkgBuildHelper(BuildHelper):
  """Class that helps in building MacOS-X packages (.pkg)."""

  def __init__(self, dependency_definition):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
    """
    super(PkgBuildHelper, self).__init__(dependency_definition)
    self._pkgbuild = os.path.join(u'/', u'usr', u'bin', u'pkgbuild')

  def _BuildDmg(self, pkg_filename, dmg_filename):
    """Builds the distributable disk image (.dmg) from the pkg.

    Args:
      pkg_filename: the name of the pkg file (which is technically
                    a directory).
      dmg_filename: the name of the dmg file.

    Returns:
      True if the build was successful, False otherwise.
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
      True if the build was successful, False otherwise.
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

  def Clean(self, source_helper):
    """Cleans the MacOS-X packages in the current directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    filenames_to_ignore = re.compile(u'^{0:s}-.*{1!s}'.format(
        source_helper.project_name, source_helper.project_version))

    # Remove files of previous versions in the format:
    # project-*version.dmg
    filenames = glob.glob(u'{0:s}-*.dmg'.format(source_helper.project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # project-*version.pkg
    filenames = glob.glob(u'{0:s}-*.pkg'.format(source_helper.project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, source_helper):
    """Retrieves the filename of one of the resulting files.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A filename of one of the resulting rpms.
    """
    return u'{0:s}-{1!s}.dmg'.format(
        source_helper.project_name, source_helper.project_version)


class LibyalPkgBuildHelper(PkgBuildHelper):
  """Class that helps in building MacOS-X packages (.pkg)."""

  def Build(self, source_helper):
    """Builds the pkg package and distributable disk image (.dmg).

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    logging.info(u'Building pkg of: {0:s}'.format(source_filename))

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    dmg_filename = u'{0:s}-{1!s}.dmg'.format(
        source_helper.project_name, source_helper.project_version)
    pkg_filename = u'{0:s}-{1!s}.pkg'.format(
        source_helper.project_name, source_helper.project_version)
    log_filename = os.path.join(u'..', self.LOG_FILENAME)

    sdks_path = os.path.join(
        u'/', u'Applications', u'Xcode.app', u'Contents', u'Developer',
        u'Platforms', u'MacOSX.platform', u'Developer', u'SDKs')

    for sub_path in [u'MacOSX10.7.sdk', u'MacOSX10.8.sdk', u'MacOSX10.9.sdk']:
      sdk_path = os.path.join(sdks_path, sub_path)
      if os.path.isdir(sub_path):
        break

    if sdk_path:
      cflags = u'CFLAGS="-isysroot {0:s}"'.format(sdk_path)
      ldflags = u'LDFLAGS="-Wl,-syslibroot,{0:s}"'.format(sdk_path)
    else:
      cflags = u''
      ldflags = u''

    if not os.path.exists(pkg_filename):
      if cflags and ldflags:
        command = (
            u'{0:s} {1:s} ./configure --prefix=/usr --enable-python '
            u'--with-pyprefix --disable-dependency-tracking > {2:s} '
            u'2>&1').format(cflags, ldflags, log_filename)
      else:
        command = (
            u'./configure --prefix=/usr --enable-python --with-pyprefix '
            u'> {0:s} 2>&1').format(log_filename)

      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      command = u'make >> {0:s} 2>&1'.format(log_filename)
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      command = u'make install DESTDIR={0:s}/tmp >> {1:s} 2>&1'.format(
          os.path.abspath(source_directory), log_filename)
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      share_doc_path = os.path.join(
          source_directory, u'tmp', u'usr', u'share', u'doc',
          source_helper.project_name)
      if not os.path.exists(share_doc_path):
        os.makedirs(share_doc_path)

      shutil.copy(os.path.join(source_directory, u'AUTHORS'), share_doc_path)
      shutil.copy(os.path.join(source_directory, u'COPYING'), share_doc_path)
      shutil.copy(os.path.join(source_directory, u'NEWS'), share_doc_path)
      shutil.copy(os.path.join(source_directory, u'README'), share_doc_path)

      project_identifier = u'com.github.libyal.{0:s}'.format(
          source_helper.project_name)
      if not self._BuildPkg(
          source_directory, project_identifier, source_helper.project_version,
          pkg_filename):
        return False

    if not self._BuildDmg(pkg_filename, dmg_filename):
      return False

    return True


class PythonModulePkgBuildHelper(PkgBuildHelper):
  """Class that helps in building MacOS-X packages (.pkg)."""

  def Build(self, source_helper):
    """Builds the pkg package and distributable disk image (.dmg).

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    logging.info(u'Building pkg of: {0:s}'.format(source_filename))

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    dmg_filename = u'{0:s}-{1!s}.dmg'.format(
        source_helper.project_name, source_helper.project_version)
    pkg_filename = u'{0:s}-{1!s}.pkg'.format(
        source_helper.project_name, source_helper.project_version)
    log_filename = os.path.join(u'..', self.LOG_FILENAME)

    if not os.path.exists(pkg_filename):
      command = u'python setup.py build > {0:s} 2>&1'.format(log_filename)
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      command = u'python setup.py install --root={0:s}/tmp > {1:s} 2>&1'.format(
          os.path.abspath(source_directory), log_filename)
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
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
        exit_code = subprocess.call(
            u'(cd {0:s} && {1:s})'.format(source_directory, command),
            shell=True)
        if exit_code != 0:
          logging.error(u'Running: "{0:s}" failed.'.format(command))
          return False

      project_identifier = source_helper.GetProjectIdentifier()
      if not self._BuildPkg(
          source_directory, project_identifier, source_helper.project_version,
          pkg_filename):
        return False

    if not self._BuildDmg(pkg_filename, dmg_filename):
      return False

    return True


class RpmBuildHelper(BuildHelper):
  """Class that helps in building rpm packages (.rpm)."""

  # TODO: determine BUILD_DEPENDENCIES from the build files?
  _BUILD_DEPENDENCIES = frozenset([
      'git',
      'binutils',
      'autoconf',
      'automake',
      'libtool',
      'gettext-devel',
      'make',
      'pkgconfig',
      'gcc',
      'gcc-c++',
      'flex',
      'byacc',
      'zlib-devel',
      'bzip2-devel',
      'openssl-devel',
      'fuse-devel',
      'rpm-build',
      'python-devel',
      'git',
      'python-dateutil',
      'python-setuptools',
      'sqlite-devel',
  ])

  def __init__(self, dependency_definition):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
    """
    super(RpmBuildHelper, self).__init__(dependency_definition)
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
      True if the build was successful, False otherwise.
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
      True if the build was successful, False otherwise.
    """
    command = u'rpmbuild -ta {0:s} > {1:s} 2>&1'.format(
        source_filename, self.LOG_FILENAME)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

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

  def _MoveRpms(self, project_name, project_version):
    """Moves the rpms from the rpmbuild directory into to current directory.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.
    """
    filenames = glob.glob(os.path.join(
        self._rpmbuild_rpms_path, u'{0:s}-*{1!s}-1.{2:s}.rpm'.format(
            project_name, project_version, self.architecture)))
    for filename in filenames:
      logging.info(u'Moving: {0:s}'.format(filename))
      shutil.move(filename, '.')

  @classmethod
  def CheckBuildDependencies(cls):
    """Checks if the build dependencies are met.

    Returns:
      A list of package names that need to be installed or an empty list.
    """
    missing_packages = []
    for package_name in cls._BUILD_DEPENDENCIES:
      if not cls.CheckIsInstalled(package_name):
        missing_packages.append(package_name)

    return missing_packages

  @classmethod
  def CheckIsInstalled(cls, package_name):
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

  def Clean(self, source_helper):
    """Cleans the rpmbuild directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    # Remove previous versions build directories.
    filenames_to_ignore = re.compile(u'{0:s}-{1!s}'.format(
        source_helper.project_name, source_helper.project_version))

    filenames = glob.glob(os.path.join(
        self.rpmbuild_path, u'BUILD', u'{0:s}-*'.format(
            source_helper.project_name)))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        shutil.rmtree(filename)

    # Remove previous versions of rpms.
    filenames_to_ignore = re.compile(
        u'{0:s}-.*{1!s}-1.{2:s}.rpm'.format(
            source_helper.project_name, source_helper.project_version,
            self.architecture))

    rpm_filenames_glob = u'{0:s}-*-1.{1:s}.rpm'.format(
        source_helper.project_name, self.architecture)

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
        source_helper.project_name, source_helper.project_version))

    filenames = glob.glob(os.path.join(
        self.rpmbuild_path, u'SRPMS',
        u'{0:s}-*-1.src.rpm'.format(source_helper.project_name)))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, source_helper):
    """Retrieves the filename of one of the resulting files.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      A filename of one of the resulting rpms.
    """
    return u'{0:s}-{1!s}-1.{2:s}.rpm'.format(
        source_helper.project_name, source_helper.project_version,
        self.architecture)


class LibyalRpmBuildHelper(RpmBuildHelper):
  """Class that helps in building libyal rpm packages (.rpm)."""

  def Build(self, source_helper):
    """Builds the rpms.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    logging.info(u'Building rpm of: {0:s}'.format(source_filename))

    # rpmbuild wants the project filename without the status indication.
    rpm_source_filename = u'{0:s}-{1!s}.tar.gz'.format(
        source_helper.project_name, source_helper.project_version)
    os.rename(source_filename, rpm_source_filename)

    build_successful = self._BuildFromSourcePackage(rpm_source_filename)

    if build_successful:
      # Move the rpms to the build directory.
      self._MoveRpms(source_helper.project_name, source_helper.project_version)

      # Remove BUILD directory.
      filename = os.path.join(
          self.rpmbuild_path, u'BUILD', u'{0:s}-{1!s}'.format(
              source_helper.project_name, source_helper.project_version))
      logging.info(u'Removing: {0:s}'.format(filename))
      shutil.rmtree(filename)

      # Remove SRPMS file.
      filename = os.path.join(
          self.rpmbuild_path, u'SRPMS', u'{0:s}-{1!s}-1.src.rpm'.format(
              source_helper.project_name, source_helper.project_version))
      logging.info(u'Removing: {0:s}'.format(filename))
      os.remove(filename)

    # Change the project filename back to the original.
    os.rename(rpm_source_filename, source_filename)

    return build_successful


class PythonModuleRpmBuildHelper(RpmBuildHelper):
  """Class that helps in building rpm packages (.rpm)."""

  def __init__(self, dependency_definition):
    """Initializes the build helper.

    Args:
      dependency_definition: the dependency definition object (instance of
                             DependencyDefinition).
    """
    super(PythonModuleRpmBuildHelper, self).__init__(dependency_definition)
    self.architecture = 'noarch'

  def Build(self, source_helper):
    """Builds the rpms.

    Args:
      source_helper: the source helper (instance of SourceHelper).

    Returns:
      True if the build was successful, False otherwise.
    """
    source_filename = source_helper.Download()
    logging.info(u'Building rpm of: {0:s}'.format(source_filename))

    source_directory = source_helper.Create()
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    command = u'python setup.py bdist_rpm > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(
        u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    # Move the rpms to the build directory.
    filenames = glob.glob(os.path.join(
        source_directory, u'dist', u'{0:s}-{1!s}-1.{2:s}.rpm'.format(
            source_helper.project_name, source_helper.project_version,
            self.architecture)))
    for filename in filenames:
      logging.info(u'Moving: {0:s}'.format(filename))
      shutil.move(filename, '.')

    return True

  def Clean(self, source_helper):
    """Cleans the build and dist directory.

    Args:
      source_helper: the source helper (instance of SourceHelper).
    """
    # Remove previous versions build directories.
    for filename in [u'build', u'dist']:
      if os.path.exists(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        shutil.rmtree(filename, True)

    # Remove previous versions of rpms.
    filenames_to_ignore = re.compile(u'{0:s}-.*{1!s}-1.{2:s}.rpm'.format(
        source_helper.project_name, source_helper.project_version,
        self.architecture))

    rpm_filenames_glob = u'{0:s}-*-1.{1:s}.rpm'.format(
        source_helper.project_name, self.architecture)

    filenames = glob.glob(rpm_filenames_glob)
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)
