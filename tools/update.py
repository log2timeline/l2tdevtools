#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to update prebuilt versions of the projects."""

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import glob
import io
import json
import logging
import os
import platform
import re
import subprocess
import sys

from l2tdevtools import presets
from l2tdevtools import projects
from l2tdevtools import versions
from l2tdevtools.download_helpers import interface


if platform.system() == 'Windows':
  import wmi  # pylint: disable=import-error


class GithubRepoDownloadHelper(interface.DownloadHelper):
  """Helps in downloading from a GitHub repository."""

  _GITHUB_REPO_API_URL = (
      'https://api.github.com/repos/log2timeline/l2tbinaries')

  _GITHUB_REPO_URL = (
      'https://github.com/log2timeline/l2tbinaries')

  def __init__(self, download_url, branch='master'):
    """Initializes a download helper.

    Args:
      download_url (str): download URL.
      branch (Optional[str]): git branch to download from.
    """
    super(GithubRepoDownloadHelper, self).__init__(download_url)
    self._branch = branch

  def _GetMachineTypeSubDirectory(
      self, preferred_machine_type=None, preferred_operating_system=None):
    """Retrieves the machine type sub directory.

    Args:
      preferred_machine_type (Optional[str]): preferred machine type, where
          None, which will auto-detect the current machine type.
      preferred_operating_system (Optional[str]): preferred operating system,
          where None, which will auto-detect the current operating system.

    Returns:
      str: machine type sub directory or None.
    """
    if preferred_operating_system:
      operating_system = preferred_operating_system
    else:
      operating_system = platform.system()

    if preferred_machine_type:
      cpu_architecture = preferred_machine_type
    else:
      cpu_architecture = platform.machine().lower()

    sub_directory = None

    if operating_system not in ('Darwin', 'Windows'):
      logging.error('Operating system: {0:s} not supported.'.format(
          operating_system))
      return None

    if (sys.version_info[0] not in (2, 3) or
        (sys.version_info[0] == 2 and sys.version_info[1] != 7) or
        (sys.version_info[0] == 3 and sys.version_info[1] != 6)):
      logging.error('Python version: {0:d}.{1:d} not supported.'.format(
          sys.version_info[0], sys.version_info[1]))
      return None

    if operating_system == 'Darwin':
      # TODO: determine macOS version.
      if cpu_architecture == 'x86_64':
        sub_directory = 'macos'

    elif operating_system == 'Windows':
      if cpu_architecture == 'x86':
        sub_directory = 'win32'

      elif cpu_architecture == 'amd64':
        sub_directory = 'win64'

    if not sub_directory:
      logging.error('CPU architecture: {0:s} not supported.'.format(
          cpu_architecture))
      return None

    return sub_directory

  def _GetDownloadURL(
      self, preferred_machine_type=None, preferred_operating_system=None,
      use_api=False):
    """Retrieves the download URL.

    Args:
      preferred_machine_type (Optional[str]): preferred machine type, where
          None, which will auto-detect the current machine type.
      preferred_operating_system (Optional[str]): preferred operating system,
          where None, which will auto-detect the current operating system.
      use_api (Optional[bool]): True if the GitHub API should be used to
          determine the download URL.

    Returns:
      str: download URL or None.
    """
    sub_directory = self._GetMachineTypeSubDirectory(
        preferred_machine_type=preferred_machine_type,
        preferred_operating_system=preferred_operating_system)
    if not sub_directory:
      return None

    if use_api:
      # TODO: add support for branch.
      download_url = '{0:s}/contents/{1:s}'.format(
          self._GITHUB_REPO_API_URL, sub_directory)

    else:
      download_url = '{0:s}/tree/{1:s}/{2:s}'.format(
          self._GITHUB_REPO_URL, self._branch, sub_directory)

    return download_url

  def GetPackageDownloadURLs(
      self, preferred_machine_type=None, preferred_operating_system=None,
      use_api=False):
    """Retrieves the package download URLs for a given system configuration.

    Args:
      preferred_machine_type (Optional[str]): preferred machine type, where
          None, which will auto-detect the current machine type.
      preferred_operating_system (Optional[str]): preferred operating system,
          where None, which will auto-detect the current operating system.
      use_api (Optional[bool]): True if the GitHub API should be used to
          determine the download URL.

    Returns:
      list[str]: list of package download URLs or None if no package download
          URLs could be determined.
    """
    download_url = self._GetDownloadURL(
        preferred_machine_type=preferred_machine_type,
        preferred_operating_system=preferred_operating_system, use_api=use_api)
    if not download_url:
      logging.info('Missing download URL.')
      return None

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return None

    # TODO: skip SHA256SUMS

    download_urls = []
    if use_api:
      # The page content consist of JSON data that contains a list of dicts.
      # Each dict consists of:
      # {
      #   "name":"PyYAML-3.11.win-amd64-py2.7.msi",
      #   "path":"win64/PyYAML-3.11.win-amd64-py2.7.msi",
      #   "sha":"8fca8c1e2549cf54bf993c55930365d01658f418",
      #   "size":196608,
      #   "url":"https://api.github.com/...",
      #   "html_url":"https://github.com/...",
      #   "git_url":"https://api.github.com/...",
      #   "download_url":"https://raw.githubusercontent.com/...",
      #   "type":"file",
      #   "_links":{
      #     "self":"https://api.github.com/...",
      #     "git":"https://api.github.com/...",
      #     "html":"https://github.com/..."
      #   }
      # }

      for directory_entry in json.loads(page_content):
        download_url = directory_entry.get('download_url', None)
        if download_url:
          download_urls.append(download_url)

    else:
      sub_directory = self._GetMachineTypeSubDirectory(
          preferred_machine_type=preferred_machine_type,
          preferred_operating_system=preferred_operating_system)
      if not sub_directory:
        return None

      # The format of the download URL is:
      # <a class="js-navigation-open" title="{title}" id="{id}" href="{path}"
      expression_string = (
          '<a class="js-navigation-open" title="[^"]*" id="[^"]*" '
          'href="([^"]*)"')
      matches = re.findall(expression_string, page_content)

      for match in matches:
        _, _, filename = match.rpartition('/')
        download_url = (
            'https://github.com/log2timeline/l2tbinaries/raw/{0:s}/{1:s}/'
            '{2:s}').format(self._branch, sub_directory, filename)
        download_urls.append(download_url)

    return download_urls


class DependencyUpdater(object):
  """Helps in updating dependencies.

  Attributes:
    operating_system (str): the operating system on which to update
        dependencies and remove previous versions.
  """

  _DOWNLOAD_URL = 'https://github.com/log2timeline/l2tbinaries/releases'

  _GIT_BRANCH_PER_TRACK = {
      'dev': 'dev',
      'stable': 'master',
      'testing': 'testing'}

  _PKG_NAME_PREFIXES = [
      'com.github.dateutil.',
      'com.github.dfvfs.',
      'com.github.erocarrer.',
      'com.github.ForensicArtifacts.',
      'com.github.kennethreitz.',
      'com.github.google.',
      'org.github.ipython.',
      'com.github.libyal.',
      'com.github.log2timeline.',
      'com.github.sleuthkit.',
      'com.google.code.p.',
      'org.samba.',
      'org.pypi.',
      'org.python.pypi.',
      'net.sourceforge.projects.']

  def __init__(
      self, download_directory='build', download_only=False,
      download_track='stable', exclude_packages=False, force_install=False,
      msi_targetdir=None, preferred_machine_type=None,
      preferred_operating_system=None, verbose_output=False):
    """Initializes the dependency updater.

    Args:
      download_directory (Optional[str]): path of the download directory.
      download_only (Optional[bool]): True if the dependency packages should
          only be downloaded.
      download_track (Optional[str]): track to download from.
      exclude_packages (Optional[bool]): True if packages should be excluded
          instead of included.
      force_install (Optional[bool]): True if the installation (update) should
          be forced.
      msi_targetdir (Optional[str]): MSI TARGETDIR property.
      preferred_machine_type (Optional[str]): preferred machine type, where
          None, which will auto-detect the current machine type.
      preferred_operating_system (Optional[str]): preferred operating system,
          where None, which will auto-detect the current operating system.
      verbose_output (Optional[bool]): True more verbose output should be
          provided.
    """
    branch = self._GIT_BRANCH_PER_TRACK.get(download_track, 'master')

    super(DependencyUpdater, self).__init__()
    self._download_directory = download_directory
    self._download_helper = GithubRepoDownloadHelper(
        self._DOWNLOAD_URL, branch=branch)
    self._download_only = download_only
    self._download_track = download_track
    self._exclude_packages = exclude_packages
    self._force_install = force_install
    self._msi_targetdir = msi_targetdir
    self._verbose_output = verbose_output

    if preferred_operating_system:
      self.operating_system = preferred_operating_system
    else:
      self.operating_system = platform.system()

    if preferred_machine_type:
      self._preferred_machine_type = preferred_machine_type.lower()
    else:
      self._preferred_machine_type = None

  def _GetPackageFilenamesAndVersions(self, package_names):
    """Determines the package filenames and versions.

    Args:
      package_names (list[str]): package names that should be updated
          if an update is available. An empty list represents all available
          packages.

    Args:
      tuple: contains:

        dict[str, str]: filenames per package or None if no filenames could
           be determined.
        dict[str, str]: versions per package or None if no version could
           be determined.
    """
    python_version_indicator = '-py{0:d}.{1:d}'.format(
        sys.version_info[0], sys.version_info[1])

    # The API is rate limited, so we scrape the web page instead.
    package_urls = self._download_helper.GetPackageDownloadURLs(
        preferred_machine_type=self._preferred_machine_type,
        preferred_operating_system=self.operating_system)
    if not package_urls:
      logging.error('Unable to determine package download URLs.')
      return None, None

    if not os.path.exists(self._download_directory):
      os.mkdir(self._download_directory)

    os.chdir(self._download_directory)

    package_filenames = {}
    package_versions = {}
    for package_url in package_urls:
      _, _, package_filename = package_url.rpartition('/')
      if package_filename.endswith('.dmg'):
        # Strip off the trailing part starting with '.dmg'.
        package_name, _, _ = package_filename.partition('.dmg')
        package_suffix = '.dmg'

      elif package_filename.endswith('.msi'):
        # Strip off the trailing part starting with '.win'.
        package_name, _, package_version = package_filename.partition('.win')
        package_suffix = '.msi'

        if ('-py' in package_version and
            python_version_indicator not in package_version):
          # Ignore packages that are for different versions of Python.
          continue

      else:
        # Ignore all other file exensions.
        continue

      if package_name.startswith('pefile-1.'):
        # We need to use the most left '-' character as the separator of the
        # name and the version, since version can contain the '-' character.
        name, _, version = package_name.partition('-')
      else:
        # We need to use the most right '-' character as the separator of the
        # name and the version, since name can contain the '-' character.
        name, _, version = package_name.rpartition('-')

      package_prefix = name
      version = version.split('.')

      if package_name.startswith('pefile-1.'):
        last_part = version.pop()
        version.extend(last_part.split('-'))

      # Ignore package names if defined.
      if package_names and (
          (not self._exclude_packages and name not in package_names) or
          (self._exclude_packages and name in package_names)):
        logging.info('Skipping: {0:s} because it was excluded'.format(name))
        continue

      if name not in package_versions:
        compare_result = 1
      else:
        compare_result = versions.CompareVersions(
            version, package_versions[name])

      if compare_result > 0:
        package_filenames[name] = package_filename
        package_versions[name] = version

      if not os.path.exists(package_filename):
        filenames = glob.glob('{0:s}*{1:s}'.format(
            package_prefix, package_suffix))
        for filename in filenames:
          if os.path.isdir(filename):
            continue

          logging.info('Removing: {0:s}'.format(filename))
          os.remove(filename)

        logging.info('Downloading: {0:s}'.format(package_filename))
        self._download_helper.DownloadFile(package_url)

    os.chdir('..')

    return package_filenames, package_versions

  def _InstallPackages(self, package_filenames, package_versions):
    """Installs packages.

    Args:
      package_filenames (dict[str, str]): filenames per package.
      package_versions (dict[str, str]): versions per package.

    Returns:
      bool: True if the installation was successful.
    """
    if self.operating_system == 'Darwin':
      return self._InstallPackagesMacOS(
          package_filenames, package_versions)

    elif self.operating_system == 'Windows':
      return self._InstallPackagesWindows(
          package_filenames, package_versions)

    return False

  def _InstallPackagesMacOS(self, package_filenames, package_versions):
    """Installs packages on macOS.

    Args:
      package_filenames (dict[str, str]): filenames per package.
      package_versions (dict[str, str]): versions per package.

    Returns:
      bool: True if the installation was successful.
    """
    result = True
    for name in package_versions.keys():
      package_filename = package_filenames[name]

      command = 'sudo /usr/bin/hdiutil attach {0:s}'.format(
          os.path.join(self._download_directory, package_filename))
      logging.info('Running: "{0:s}"'.format(command))
      exit_code = subprocess.call(command, shell=True)
      if exit_code != 0:
        logging.error('Running: "{0:s}" failed.'.format(command))
        result = False
        continue

      volume_path = '/Volumes/{0:s}.pkg'.format(package_filename[:-4])
      if not os.path.exists(volume_path):
        logging.error('Missing volume: {0:s}.'.format(volume_path))
        result = False
        continue

      pkg_file = '{0:s}/{1:s}.pkg'.format(volume_path, package_filename[:-4])
      if not os.path.exists(pkg_file):
        logging.error('Missing pkg file: {0:s}.'.format(pkg_file))
        result = False
        continue

      command = 'sudo /usr/sbin/installer -target / -pkg {0:s}'.format(
          pkg_file)
      logging.info('Running: "{0:s}"'.format(command))
      exit_code = subprocess.call(command, shell=True)
      if exit_code != 0:
        logging.error('Running: "{0:s}" failed.'.format(command))
        result = False

      command = 'sudo /usr/bin/hdiutil detach {0:s}'.format(volume_path)
      logging.info('Running: "{0:s}"'.format(command))
      exit_code = subprocess.call(command, shell=True)
      if exit_code != 0:
        logging.error('Running: "{0:s}" failed.'.format(command))
        result = False

    return result

  def _InstallPackagesWindows(self, package_filenames, package_versions):
    """Installs packages on Windows.

    Args:
      package_filenames (dict[str, str]): filenames per package.
      package_versions (dict[str, str]): versions per package.

    Returns:
      bool: True if the installation was successful.
    """
    log_file = 'msiexec.log'
    if os.path.exists(log_file):
      os.remove(log_file)

    if self._msi_targetdir:
      parameters = ' TARGETDIR="{0:s}"'.format(self._msi_targetdir)
    else:
      parameters = ''

    result = True
    for name, version in package_versions.items():
      # TODO: add RunAs ?
      package_filename = package_filenames[name]
      package_path = os.path.join(self._download_directory, package_filename)
      command = 'msiexec.exe /i {0:s} /q /log {1:s}{2:s}'.format(
          package_path, log_file, parameters)
      logging.info('Installing: {0:s} {1:s}'.format(name, '.'.join(version)))
      exit_code = subprocess.call(command, shell=False)
      if exit_code != 0:
        logging.error('Running: "{0:s}" failed.'.format(command))
        result = False

        if self._verbose_output:
          with io.open(log_file, 'r', encoding='utf-16-le') as file_object:
            log_file_contents = file_object.read()
            print(log_file_contents.encode('ascii', errors='replace'))

    return result

  def _UninstallPackages(self, package_versions):
    """Uninstalls packages if necessary.

    It is preferred that the system package manager handles this, however not
    every operating system seems to have a package manager capable to do so.

    Args:
      package_versions (dict[str, str]): versions per package.

    Returns:
      bool: True if the uninstall was successful.
    """
    if self.operating_system == 'Darwin':
      return self._UninstallPackagesMacOSX(package_versions)

    elif self.operating_system == 'Windows':
      return self._UninstallPackagesWindows(package_versions)

    return False

  def _UninstallPackagesMacOSX(self, package_versions):
    """Uninstalls packages on Mac OS X.

    Args:
      package_versions (dict[str, str]): versions per package.

    Returns:
      bool: True if the uninstall was successful.
    """
    command = '/usr/sbin/pkgutil --packages'
    logging.info('Running: "{0:s}"'.format(command))
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    if process.returncode is None:
      packages, _ = process.communicate()
    else:
      packages = ''

    if process.returncode != 0:
      logging.error('Running: "{0:s}" failed.'.format(command))
      return False

    result = True

    for package_name in packages.split('\n'):
      if not package_name:
        continue

      matching_prefix = None
      for prefix in self._PKG_NAME_PREFIXES:
        if package_name.startswith(prefix):
          matching_prefix = prefix

      if matching_prefix:
        name = package_name[len(matching_prefix):]

        # Detect the PackageMaker naming convention.
        if name.endswith('.pkg'):
          _, _, sub_name = name[:-4].rpartition('.')
          is_package_maker_pkg = True
        else:
          is_package_maker_pkg = False
        name, _, _ = name.partition('.')

        if name in package_versions:
          # Determine the package version.
          command = '/usr/sbin/pkgutil --pkg-info {0:s}'.format(package_name)
          logging.info('Running: "{0:s}"'.format(command))
          process = subprocess.Popen(
              command, stdout=subprocess.PIPE, shell=True)
          if process.returncode is None:
            package_info, _ = process.communicate()
          else:
            package_info = ''

          if process.returncode != 0:
            logging.error('Running: "{0:s}" failed.'.format(command))
            result = False
            continue

          location = None
          version = None
          volume = None
          for attribute in package_info.split('\n'):
            if attribute.startswith('location: '):
              _, _, location = attribute.rpartition('location: ')

            elif attribute.startswith('version: '):
              _, _, version = attribute.rpartition('version: ')

            elif attribute.startswith('volume: '):
              _, _, volume = attribute.rpartition('volume: ')

          if self._force_install:
            compare_result = -1
          elif name not in package_versions:
            compare_result = 1
          elif name in ('pytsk', 'pytsk3'):
            # We cannot really tell by the version number that pytsk3 needs to
            # be updated, so just uninstall and update it any way.
            compare_result = -1
          else:
            version_tuple = version.split('.')
            compare_result = versions.CompareVersions(
                version_tuple, package_versions[name])
            if compare_result >= 0:
              # The latest or newer version is already installed.
              del package_versions[name]

          if compare_result < 0:
            # Determine the files in the package.
            command = '/usr/sbin/pkgutil --files {0:s}'.format(package_name)
            logging.info('Running: "{0:s}"'.format(command))
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, shell=True)
            if process.returncode is None:
              package_files, _ = process.communicate()
            else:
              package_files = ''

            if process.returncode != 0:
              logging.error('Running: "{0:s}" failed.'.format(command))
              result = False
              continue

            directories = []
            files = []
            for filename in package_files.split('\n'):
              if is_package_maker_pkg:
                filename = '{0:s}{1:s}/{2:s}/{3:s}'.format(
                    volume, location, sub_name, filename)
              else:
                filename = '{0:s}{1:s}'.format(location, filename)

              if os.path.isdir(filename):
                directories.append(filename)
              else:
                files.append(filename)

            logging.info('Removing: {0:s} {1:s}'.format(name, version))
            for filename in files:
              if os.path.exists(filename):
                os.remove(filename)

            for filename in directories:
              if os.path.exists(filename):
                try:
                  os.rmdir(filename)
                except OSError:
                  # Ignore directories that are not empty.
                  pass

            command = '/usr/sbin/pkgutil --forget {0:s}'.format(
                package_name)
            exit_code = subprocess.call(command, shell=True)
            if exit_code != 0:
              logging.error('Running: "{0:s}" failed.'.format(command))
              result = False

    return result

  def _UninstallPackagesWindows(self, package_versions):
    """Uninstalls packages on Windows.

    Args:
      package_versions (dict[str, str]): versions per package.

    Returns:
      bool: True if the uninstall was successful.
    """
    # Tuple of packge name suffix, machine type, Python version
    package_info = (
        ('.win32.msi', 'x86', None),
        ('.win32-py2.7.msi', 'x86', 2),
        ('.win32-py3.6.msi', 'x86', 3),
        ('.win-amd64.msi', 'amd64', None),
        ('.win-amd64-py2.7.msi', 'amd64', 2),
        ('.win-amd64-py3.6.msi', 'amd64', 3))

    connection = wmi.WMI()

    query = 'SELECT PackageName FROM Win32_Product'
    for product in connection.query(query):
      name = getattr(product, 'PackageName', '')

      has_known_suffix = False
      machine_type = None
      python_version = None
      for name_suffix, machine_type, python_version in package_info:
        has_known_suffix = name.endswith(name_suffix)
        if has_known_suffix:
          name = name[:-len(name_suffix)]
          break

      if not has_known_suffix:
        continue

      if (self._preferred_machine_type and
          self._preferred_machine_type != machine_type):
        continue

      # TODO: improve this check to support Python 3.
      if python_version and python_version != 2:
        continue

      name, _, version = name.rpartition('-')

      found_package = name in package_versions

      version_tuple = version.split('.')
      if self._force_install:
        compare_result = -1
      elif not found_package:
        compare_result = 1
      else:
        compare_result = versions.CompareVersions(
            version_tuple, package_versions[name])
        if compare_result >= 0:
          # The latest or newer version is already installed.
          del package_versions[name]

      if not found_package and name.startswith('py'):
        # Remove libyal Python packages using the old naming convention.
        new_name = 'lib{0:s}-python'.format(name[2:])
        found_package = new_name in package_versions
        if found_package:
          compare_result = -1

      if found_package and compare_result < 0:
        logging.info('Removing: {0:s} {1:s}'.format(name, version))
        product.Uninstall()

    return True

  def UpdatePackages(self, package_names):
    """Updates packages.

    Args:
      package_names (list[str]): package names that should be updated
          if an update is available. An empty list represents all available
          packages.

    Returns:
      bool: True if the update was successful.
    """
    package_filenames, package_versions = self._GetPackageFilenamesAndVersions(
        package_names)
    if not package_filenames:
      logging.error('No packages found.')
      return False

    if self._download_only:
      return True

    if not self._UninstallPackages(package_versions):
      logging.error('Unable to uninstall packages.')
      return False

    return self._InstallPackages(package_filenames, package_versions)


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  tracks = ['dev', 'stable', 'testing']

  argument_parser = argparse.ArgumentParser(description=(
      'Installs the latest versions of project dependencies.'))

  argument_parser.add_argument(
      '-c', '--config', dest='config_path', action='store',
      metavar='CONFIG_PATH', default=None, help=(
          'path of the directory containing the build configuration '
          'files e.g. projects.ini.'))

  argument_parser.add_argument(
      '--download-directory', '--download_directory', action='store',
      metavar='DIRECTORY', dest='download_directory', type=str,
      default='build', help='The location of the download directory.')

  argument_parser.add_argument(
      '--download-only', '--download_only', action='store_true',
      dest='download_only', default=False, help=(
          'Only download the dependencies. The default behavior is to '
          'download and update the dependencies.'))

  argument_parser.add_argument(
      '-e', '--exclude', action='store_true', dest='exclude_packages',
      default=False, help=(
          'Excludes the package names instead of including them.'))

  argument_parser.add_argument(
      '-f', '--force', action='store_true', dest='force_install',
      default=False, help=(
          'Force installation. This option removes existing versions '
          'of installed dependencies. The default behavior is to only'
          'install a dependency if not or an older version is installed.'))

  argument_parser.add_argument(
      '--machine-type', '--machine_type', action='store', metavar='TYPE',
      dest='machine_type', type=str, default=None, help=(
          'Manually sets the machine type instead of using the value returned '
          'by platform.machine(). Usage of this argument is not recommended '
          'unless want to force the installation of one machine type e.g. '
          '\'x86\' onto another \'amd64\'.'))

  argument_parser.add_argument(
      '--msi-targetdir', '--msi_targetdir', action='store', metavar='TYPE',
      dest='msi_targetdir', type=str, default=None, help=(
          'Manually sets the MSI TARGETDIR property. Usage of this argument '
          'is not recommended unless want to force the installation of the '
          'MSIs into different directory than the system default.'))

  argument_parser.add_argument(
      '--preset', dest='preset', action='store',
      metavar='PRESET_NAME', default=None, help=(
          'name of the preset of project names to update. The default is to '
          'build all project defined in the projects.ini configuration file. '
          'The presets are defined in the preset.ini configuration file.'))

  argument_parser.add_argument(
      '-t', '--track', dest='track', action='store', metavar='TRACK',
      default='stable', choices=sorted(tracks), help=(
          'the l2tbinaries track to download from. The default is stable.'))

  argument_parser.add_argument(
      '-v', '--verbose', dest='verbose', action='store_true', default=False,
      help='have more verbose output.')

  argument_parser.add_argument(
      'project_names', nargs='*', action='store', metavar='NAME',
      type=str, help=(
          'Optional project names which should be updated if an update is '
          'available. The corresponding package names are derived from '
          'the projects.ini configuration file. If no value is provided '
          'all available packages are updated.'))

  options = argument_parser.parse_args()

  config_path = options.config_path
  if not config_path:
    config_path = os.path.dirname(__file__)
    config_path = os.path.dirname(config_path)
    config_path = os.path.join(config_path, 'data')

  presets_file = os.path.join(config_path, 'presets.ini')
  if options.preset and not os.path.exists(presets_file):
    print('No such config file: {0:s}.'.format(presets_file))
    print('')
    return False

  projects_file = os.path.join(config_path, 'projects.ini')
  if not os.path.exists(projects_file):
    print('No such config file: {0:s}.'.format(projects_file))
    print('')
    return False

  logging.basicConfig(
      level=logging.INFO, format='[%(levelname)s] %(message)s')

  project_names = []
  if options.preset:
    with io.open(presets_file, 'r', encoding='utf-8') as file_object:
      preset_definition_reader = presets.PresetDefinitionReader()
      for preset_definition in preset_definition_reader.Read(file_object):
        if preset_definition.name == options.preset:
          project_names = preset_definition.project_names
          break

    if not project_names:
      print('Undefined preset: {0:s}'.format(options.preset))
      print('')
      return False

  elif options.project_names:
    project_names = options.project_names

  dependency_updater = DependencyUpdater(
      download_directory=options.download_directory,
      download_only=options.download_only,
      download_track=options.track,
      exclude_packages=options.exclude_packages,
      force_install=options.force_install,
      msi_targetdir=options.msi_targetdir,
      preferred_machine_type=options.machine_type,
      verbose_output=options.verbose)

  project_definitions = {}
  with io.open(projects_file, 'r', encoding='utf-8') as file_object:
    project_definition_reader = projects.ProjectDefinitionReader()
    for project_definition in project_definition_reader.Read(file_object):
      project_definitions[project_definition.name] = project_definition

  package_names = []
  for project_name in project_names:
    project_definition = project_definitions.get(project_name, None)
    if not project_definition:
      logging.error('Missing definition for project: {0:s}'.format(
          project_name))
      continue

    package_name = project_name
    if (dependency_updater.operating_system == 'Windows' and
        project_definition.msi_name):
      package_name = project_definition.msi_name

    package_names.append(package_name)

  return dependency_updater.UpdatePackages(package_names)


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
