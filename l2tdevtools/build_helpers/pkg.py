# -*- coding: utf-8 -*-
"""Helper for building projects from source."""

from __future__ import unicode_literals

import glob
import logging
import os
import re
import shutil
import subprocess

from l2tdevtools.build_helpers import interface


class PKGBuildHelper(interface.BuildHelper):
  """Helper to build MacOS-X packages (.pkg)."""

  def __init__(self, project_definition, l2tdevtools_path):
    """Initializes a build helper.

    Args:
      project_definition (ProjectDefinition): project definition.
      l2tdevtools_path (str): path to the l2tdevtools directory.
    """
    super(PKGBuildHelper, self).__init__(project_definition, l2tdevtools_path)
    self._pkgbuild = os.path.join('/', 'usr', 'bin', 'pkgbuild')

  def _BuildDmg(self, pkg_filename, dmg_filename):
    """Builds the distributable disk image (.dmg) from the pkg.

    Args:
      pkg_filename (str): name of the pkg file (which is technically
          a directory).
      dmg_filename (str): name of the dmg file.

    Returns:
      bool: True if successful, False otherwise.
    """
    command = (
        'hdiutil create {0:s} -srcfolder {1:s} -fs HFS+').format(
            dmg_filename, pkg_filename)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _BuildPKG(
      self, source_directory, project_identifier, project_version,
      pkg_filename):
    """Builds the distributable disk image (.dmg) from the pkg.

    Args:
      source_directory (str): name of the source directory.
      project_identifier (str): project identifier.
      project_version (str): version of the project.
      pkg_filename (str): name of the pkg file (which is technically
          a directory).

    Returns:
      bool: True if successful, False otherwise.
    """
    command = (
        '{0:s} --root {1:s}/tmp/ --identifier {2:s} '
        '--version {3!s} --ownership recommended {4:s}').format(
            self._pkgbuild, source_directory, project_identifier,
            project_version, pkg_filename)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def CheckBuildDependencies(self):
    """Checks if the build dependencies are met.

    Returns:
      list[str]: build dependency names that are not met or an empty list.
    """
    # TODO: implement build dependency check.
    return []

  def CheckBuildRequired(self, source_helper_object):
    """Checks if a build is required.

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if a build is required, False otherwise.
    """
    project_version = source_helper_object.GetProjectVersion()

    dmg_filename = '{0:s}-{1!s}.dmg'.format(
        source_helper_object.project_name, project_version)

    return not os.path.exists(dmg_filename)

  def Clean(self, source_helper_object):
    """Cleans the MacOS-X packages in the current directory.

    Args:
      source_helper_object (SourceHelper): source helper.
    """
    project_version = source_helper_object.GetProjectVersion()

    filenames_to_ignore = '^{0:s}-.*{1!s}'.format(
        source_helper_object.project_name, project_version)
    filenames_to_ignore = re.compile(filenames_to_ignore)

    # Remove files of previous versions in the format:
    # project-*version.dmg
    filenames_glob = '{0:s}-*.dmg'.format(source_helper_object.project_name)
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # project-*version.pkg
    filenames_glob = '{0:s}-*.pkg'.format(source_helper_object.project_name)
    filenames = glob.glob(filenames_glob)

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info('Removing: {0:s}'.format(filename))
        os.remove(filename)


class ConfigureMakePKGBuildHelper(PKGBuildHelper):
  """Helper to build MacOS-X packages (.pkg)."""

  _DOC_FILENAMES = frozenset([
      'AUTHORS',
      'AUTHORS.txt',
      'COPYING',
      'COPYING.txt',
      'LICENSE',
      'LICENSE.txt',
      'NEWS',
      'NEWS.txt',
      'README',
      'README.md',
      'README.txt'])

  _SDK_VERSIONS = ('10.7', '10.8', '10.9', '10.10', '10.11', '10.12')

  def Build(self, source_helper_object):
    """Builds the pkg package and distributable disk image (.dmg).

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info('Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    project_version = source_helper_object.GetProjectVersion()

    logging.info('Building pkg of: {0:s}'.format(source_filename))

    if self._project_definition.patches:
      # TODO: add self._ApplyPatches
      pass

    dmg_filename = '{0:s}-{1!s}.dmg'.format(
        source_helper_object.project_name, project_version)
    pkg_filename = '{0:s}-{1!s}.pkg'.format(
        source_helper_object.project_name, project_version)
    log_file_path = os.path.join('..', self.LOG_FILENAME)

    sdks_path = os.path.join(
        '/', 'Applications', 'Xcode.app', 'Contents', 'Developer',
        'Platforms', 'MacOSX.platform', 'Developer', 'SDKs')

    sdk_path = None
    for sdk_version in self._SDK_VERSIONS:
      sdk_sub_path = 'MacOSX{0:s}.sdk'.format(sdk_version)
      if os.path.isdir(sdk_sub_path):
        sdk_path = os.path.join(sdks_path, sdk_sub_path)
        break

    if sdk_path:
      cflags = 'CFLAGS="-isysroot {0:s}"'.format(sdk_path)
      ldflags = 'LDFLAGS="-Wl,-syslibroot,{0:s}"'.format(sdk_path)
    else:
      cflags = ''
      ldflags = ''

    if not os.path.exists(pkg_filename):
      prefix = '/usr/local'
      configure_options = ''
      if self._project_definition.pkg_configure_options:
        configure_options = ' '.join(
            self._project_definition.pkg_configure_options)

      elif self._project_definition.configure_options:
        configure_options = ' '.join(
            self._project_definition.configure_options)

      if cflags and ldflags:
        command = (
            '{0:s} {1:s} ./configure --prefix={2:s} {3:s} '
            '--disable-dependency-tracking > {4:s} 2>&1').format(
                cflags, ldflags, prefix, configure_options, log_file_path)
      else:
        command = (
            './configure --prefix={0:s} {1:s} > {2:s} 2>&1').format(
                prefix, configure_options, log_file_path)

      exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
          source_directory, command), shell=True)
      if exit_code != 0:
        logging.error('Running: "{0:s}" failed.'.format(command))
        return False

      command = 'make >> {0:s} 2>&1'.format(log_file_path)
      exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
          source_directory, command), shell=True)
      if exit_code != 0:
        logging.error('Running: "{0:s}" failed.'.format(command))
        return False

      command = 'make install DESTDIR={0:s}/tmp >> {1:s} 2>&1'.format(
          os.path.abspath(source_directory), log_file_path)
      exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
          source_directory, command), shell=True)
      if exit_code != 0:
        logging.error('Running: "{0:s}" failed.'.format(command))
        return False

      share_doc_path = os.path.join(
          source_directory, 'tmp', 'usr', 'local', 'share', 'doc',
          source_helper_object.project_name)
      if not os.path.exists(share_doc_path):
        os.makedirs(share_doc_path)

      for doc_filename in self._DOC_FILENAMES:
        doc_path = os.path.join(source_directory, doc_filename)
        if os.path.exists(doc_path):
          shutil.copy(doc_path, share_doc_path)

      licenses_directory = os.path.join(source_directory, 'licenses')
      if os.path.isdir(licenses_directory):
        filenames_glob = os.path.join(licenses_directory, '*')
        filenames = glob.glob(filenames_glob)

        for doc_path in filenames:
          shutil.copy(doc_path, share_doc_path)

      project_identifier = 'com.github.libyal.{0:s}'.format(
          source_helper_object.project_name)
      if not self._BuildPKG(
          source_directory, project_identifier, project_version, pkg_filename):
        return False

    if not self._BuildDmg(pkg_filename, dmg_filename):
      return False

    return True


class SetupPyPKGBuildHelper(PKGBuildHelper):
  """Helper to build MacOS-X packages (.pkg)."""

  def Build(self, source_helper_object):
    """Builds the pkg package and distributable disk image (.dmg).

    Args:
      source_helper_object (SourceHelper): source helper.

    Returns:
      bool: True if successful, False otherwise.
    """
    source_filename = source_helper_object.Download()
    if not source_filename:
      logging.info('Download of: {0:s} failed'.format(
          source_helper_object.project_name))
      return False

    source_directory = source_helper_object.Create()
    if not source_directory:
      logging.error(
          'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    project_version = source_helper_object.GetProjectVersion()

    logging.info('Building pkg of: {0:s}'.format(source_filename))

    if self._project_definition.patches:
      # TODO: add self._ApplyPatches
      pass

    dmg_filename = '{0:s}-{1!s}.dmg'.format(
        source_helper_object.project_name, project_version)
    pkg_filename = '{0:s}-{1!s}.pkg'.format(
        source_helper_object.project_name, project_version)
    log_file_path = os.path.join('..', self.LOG_FILENAME)

    if not os.path.exists(pkg_filename):
      command = 'python setup.py build > {0:s} 2>&1'.format(log_file_path)
      exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
          source_directory, command), shell=True)
      if exit_code != 0:
        logging.error('Running: "{0:s}" failed.'.format(command))
        return False

      command = (
          'python setup.py install --root={0:s}/tmp '
          '--install-data=/usr/local > {1:s} 2>&1').format(
              os.path.abspath(source_directory), log_file_path)
      exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
          source_directory, command), shell=True)
      if exit_code != 0:
        logging.error('Running: "{0:s}" failed.'.format(command))
        return False

      # Copy the license file to the egg-info sub directory.
      for license_file in (
          'COPYING', 'LICENSE', 'LICENSE.TXT', 'LICENSE.txt'):
        if not os.path.exists(os.path.join(source_directory, license_file)):
          continue

        command = (
            'find ./tmp -type d -name \\*.egg-info -exec cp {0:s} {{}} '
            '\\;').format(license_file)
        exit_code = subprocess.call('(cd {0:s} && {1:s})'.format(
            source_directory, command), shell=True)
        if exit_code != 0:
          logging.error('Running: "{0:s}" failed.'.format(command))
          return False

      project_identifier = source_helper_object.GetProjectIdentifier()
      if not self._BuildPKG(
          source_directory, project_identifier, project_version, pkg_filename):
        return False

    if not self._BuildDmg(pkg_filename, dmg_filename):
      return False

    return True
