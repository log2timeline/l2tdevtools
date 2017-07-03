#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to update prebuilt versions of the projects."""

from __future__ import print_function
import argparse
import glob
import json
import logging
import os
import platform
import re
import subprocess
import sys

from l2tdevtools import download_helper
from l2tdevtools import presets
from l2tdevtools import projects


if platform.system() == u'Windows':
  import wmi  # pylint: disable=import-error


def CompareVersions(first_version_list, second_version_list):
  """Compares two lists containing version parts.

  Note that the version parts can contain alpha numeric characters.

  Args:
    first_version_list (list[str]): first version parts.
    second_version_list (list[str]): second version parts.

  Returns:
    int: 1 if the first is larger than the second, -1 if the first is smaller
        than the second, or 0 if the first and second are equal.
  """
  first_version_list_length = len(first_version_list)
  second_version_list_length = len(second_version_list)

  for index in range(0, first_version_list_length):
    if index >= second_version_list_length:
      return 1

    try:
      first_version_part = int(first_version_list[index], 10)
      second_version_part = int(second_version_list[index], 10)
    except ValueError:
      first_version_part = first_version_list[index]
      second_version_part = second_version_list[index]

    if first_version_part > second_version_part:
      return 1
    elif first_version_part < second_version_part:
      return -1

  if first_version_list_length < second_version_list_length:
    return -1

  return 0


class GithubRepoDownloadHelper(download_helper.DownloadHelper):
  """Class that helps in downloading from a GitHub repository."""

  _GITHUB_REPO_API_URL = (
      u'https://api.github.com/repos/log2timeline/l2tbinaries')

  _GITHUB_REPO_URL = (
      u'https://github.com/log2timeline/l2tbinaries')

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

    if operating_system == u'Darwin':
      # TODO: determine macOS version.
      if cpu_architecture != u'x86_64':
        logging.error(u'CPU architecture: {0:s} not supported.'.format(
            cpu_architecture))
        return

      sub_directory = u'macosx'

    elif operating_system == u'Linux':
      linux_name, linux_version, _ = platform.linux_distribution()
      logging.error(u'Linux: {0:s} {1:s} not supported.'.format(
          linux_name, linux_version))

      if linux_name == u'Ubuntu':
        wiki_url = (
            u'https://github.com/log2timeline/plaso/wiki/Dependencies---Ubuntu'
            u'#prepackaged-dependencies')
        logging.error(
            u'Use the gift PPA instead. For more info see: {0:s}'.format(
                wiki_url))

      return

    elif operating_system == u'Windows':
      if cpu_architecture == u'x86':
        sub_directory = u'win32'

      elif cpu_architecture == u'amd64':
        sub_directory = u'win64'

      else:
        logging.error(u'CPU architecture: {0:s} not supported.'.format(
            cpu_architecture))
        return

    else:
      logging.error(u'Operating system: {0:s} not supported.'.format(
          operating_system))
      return

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
      use_api (Optional[bool]): True if the github API should be used to
          determine the download URL.

    Returns:
      str: download URL or None.
    """
    sub_directory = self._GetMachineTypeSubDirectory(
        preferred_machine_type=preferred_machine_type,
        preferred_operating_system=preferred_operating_system)
    if not sub_directory:
      return

    if use_api:
      download_url = u'{0:s}/contents/{1:s}'.format(
          self._GITHUB_REPO_API_URL, sub_directory)

    else:
      download_url = u'{0:s}/tree/master/{1:s}'.format(
          self._GITHUB_REPO_URL, sub_directory)

    return download_url

  def GetPackageDownloadURLs(
      self, preferred_machine_type=None, preferred_operating_system=None,
      use_api=False):
    """Retrieves the package downloads URL for a given URL.

    Args:
      preferred_machine_type (Optional[str]): preferred machine type, where
          None, which will auto-detect the current machine type.
      preferred_operating_system (Optional[str]): preferred operating system,
          where None, which will auto-detect the current operating system.
      use_api (Optional[bool]): True if the github API should be used to
          determine the download URL.

    Returns:
      list[str]: list of package download URLs or None.
    """
    download_url = self._GetDownloadURL(
        preferred_machine_type=preferred_machine_type,
        preferred_operating_system=preferred_operating_system, use_api=use_api)
    if not download_url:
      logging.info(u'Missing download URL.')
      return

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

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
        download_url = directory_entry.get(u'download_url', None)
        if download_url:
          download_urls.append(download_url)

    else:
      sub_directory = self._GetMachineTypeSubDirectory(
          preferred_machine_type=preferred_machine_type,
          preferred_operating_system=preferred_operating_system)
      if not sub_directory:
        return

      # The format of the download URL is:
      # <a href="{path}" class="js-directory-link"
      # <a href="{path}" class="js-directory-link js-navigation-open"
      # <a href="{path}" class="js-navigation-open"
      expression_string = (
          u'<a href="([^"]*)" class="(js-directory-link|js-navigation-open)')
      matches = re.findall(expression_string, page_content)

      for match_tuple in matches:
        _, _, filename = match_tuple[0].rpartition(u'/')
        download_url = (
            u'https://github.com/log2timeline/l2tbinaries/raw/master/{0:s}/'
            u'{1:s}').format(sub_directory, filename)
        download_urls.append(download_url)

    return download_urls


class DependencyUpdater(object):
  """Class that helps in updating dependencies.

  Attributes:
    operating_system (str): the operating system on which to update
        dependencies and remove previous versions.
  """

  _DOWNLOAD_URL = u'https://github.com/log2timeline/l2tbinaries/releases'

  _PKG_NAME_PREFIXES = [
      u'com.github.dateutil.',
      u'com.github.dfvfs.',
      u'com.github.erocarrer.',
      u'com.github.ForensicArtifacts.',
      u'com.github.kennethreitz.',
      u'com.github.google.',
      u'org.github.ipython.',
      u'com.github.libyal.',
      u'com.github.log2timeline.',
      u'com.github.sleuthkit.',
      u'com.google.code.p.',
      u'org.samba.',
      u'org.python.pypi.',
      u'net.sourceforge.projects.']

  def __init__(
      self, download_directory=u'build', download_only=False,
      exclude_packages=False, force_install=False, msi_targetdir=None,
      preferred_machine_type=None, preferred_operating_system=None,
      verbose_output=False):
    """Initializes the dependency updater.

    Args:
      download_directory (Optional[str]): path of the download directory.
      download_only (Optional[bool]): True if the dependency packages should
          only be downloaded.
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
    super(DependencyUpdater, self).__init__()
    self._download_directory = download_directory
    self._download_helper = GithubRepoDownloadHelper(self._DOWNLOAD_URL)
    self._download_only = download_only
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

        dict[str, str]: filenames per package.
        dict[str, str]: versions per package.
    """
    # The API is rate limited, so we scrape the web page instead.
    package_urls = self._download_helper.GetPackageDownloadURLs(
        preferred_machine_type=self._preferred_machine_type,
        preferred_operating_system=self.operating_system)
    if not package_urls:
      logging.error(u'Unable to determine package download URLs.')
      return None, None

    if not os.path.exists(self._download_directory):
      os.mkdir(self._download_directory)

    os.chdir(self._download_directory)

    package_filenames = {}
    package_versions = {}
    for package_url in package_urls:
      _, _, package_filename = package_url.rpartition(u'/')
      if package_filename.endswith(u'.dmg'):
        # Strip off the trailing part starting with '.dmg'.
        package_name, _, _ = package_filename.partition(u'.dmg')
        package_suffix = u'.dmg'

      elif package_filename.endswith(u'.msi'):
        # Strip off the trailing part starting with '.win'.
        package_name, _, _ = package_filename.partition(u'.win')
        package_suffix = u'.msi'

      else:
        # Ignore all other file exensions.
        continue

      if package_name.startswith(u'pefile-1.'):
        # We need to use the most left '-' character as the separator of the
        # name and the version, since version can contain the '-' character.
        name, _, version = package_name.partition(u'-')
      else:
        # We need to use the most right '-' character as the separator of the
        # name and the version, since name can contain the '-' character.
        name, _, version = package_name.rpartition(u'-')

      package_prefix = name
      version = version.split(u'.')

      if package_name.startswith(u'pefile-1.'):
        last_part = version.pop()
        version.extend(last_part.split(u'-'))

      # Ignore package names if defined.
      if package_names and (
          (not self._exclude_packages and name not in package_names) or
          (self._exclude_packages and name in package_names)):
        logging.info(u'Skipping: {0:s} because it was excluded'.format(name))
        continue

      if name not in package_versions:
        compare_result = 1
      else:
        compare_result = CompareVersions(version, package_versions[name])

      if compare_result > 0:
        package_filenames[name] = package_filename
        package_versions[name] = version

      if not os.path.exists(package_filename):
        filenames = glob.glob(u'{0:s}*{1:s}'.format(
            package_prefix, package_suffix))
        for filename in filenames:
          if os.path.isdir(filename):
            continue

          logging.info(u'Removing: {0:s}'.format(filename))
          os.remove(filename)

        logging.info(u'Downloading: {0:s}'.format(package_filename))
        self._download_helper.DownloadFile(package_url)

    os.chdir(u'..')

    return package_filenames, package_versions

  def _InstallPackages(self, package_filenames, package_versions):
    """Installs packages.

    Args:
      package_filenames (dict[str, str]): filenames per package.
      package_versions (dict[str, str]): versions per package.

    Returns:
      bool: True if the installation was successful.
    """
    if self.operating_system == u'Darwin':
      return self._InstallPackagesMacOS(
          package_filenames, package_versions)

    elif self.operating_system == u'Windows':
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
    for name, _ in package_versions.iteritems():
      package_filename = package_filenames[name]

      command = u'sudo /usr/bin/hdiutil attach {0:s}'.format(
          os.path.join(self._download_directory, package_filename))
      logging.info(u'Running: "{0:s}"'.format(command))
      exit_code = subprocess.call(command, shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        result = False
        continue

      volume_path = u'/Volumes/{0:s}.pkg'.format(package_filename[:-4])
      if not os.path.exists(volume_path):
        logging.error(u'Missing volume: {0:s}.'.format(volume_path))
        result = False
        continue

      pkg_file = u'{0:s}/{1:s}.pkg'.format(volume_path, package_filename[:-4])
      if not os.path.exists(pkg_file):
        logging.error(u'Missing pkg file: {0:s}.'.format(pkg_file))
        result = False
        continue

      command = u'sudo /usr/sbin/installer -target / -pkg {0:s}'.format(
          pkg_file)
      logging.info(u'Running: "{0:s}"'.format(command))
      exit_code = subprocess.call(command, shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        result = False

      command = u'sudo /usr/bin/hdiutil detach {0:s}'.format(volume_path)
      logging.info(u'Running: "{0:s}"'.format(command))
      exit_code = subprocess.call(command, shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
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
    log_file = u'msiexec.log'
    if os.path.exists(log_file):
      os.remove(log_file)

    if self._msi_targetdir:
      parameters = u' TARGETDIR={0:s}'.format(self._msi_targetdir)
    else:
      parameters = u''

    result = True
    for name, version in package_versions.iteritems():
      # TODO: add RunAs ?
      package_filename = package_filenames[name]
      package_path = os.path.join(self._download_directory, package_filename)
      command = u'msiexec.exe /i {0:s} /q /log {1:s}{2:s}'.format(
          package_path, log_file, parameters)
      logging.info(u'Installing: {0:s} {1:s}'.format(name, u'.'.join(version)))
      exit_code = subprocess.call(command, shell=False)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        result = False

        if self._verbose_output:
          with open(log_file, 'r') as file_object:
            log_file_contents = file_object.read()
            log_file_contents = log_file_contents.decode(u'utf-16-le')
            print(log_file_contents.encode(u'ascii', errors=u'replace'))

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
    if self.operating_system == u'Darwin':
      return self._UninstallPackagesMacOSX(package_versions)

    elif self.operating_system == u'Windows':
      return self._UninstallPackagesWindows(package_versions)

    return True

  def _UninstallPackagesMacOSX(self, package_versions):
    """Uninstalls packages on Mac OS X.

    Args:
      package_versions (dict[str, str]): versions per package.

    Returns:
      bool: True if the uninstall was successful.
    """
    command = u'/usr/sbin/pkgutil --packages'
    logging.info(u'Running: "{0:s}"'.format(command))
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    if process.returncode is None:
      packages, _ = process.communicate()
    else:
      packages = u''

    if process.returncode != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
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
        if name.endswith(u'.pkg'):
          _, _, sub_name = name[:-4].rpartition(u'.')
          is_package_maker_pkg = True
        else:
          is_package_maker_pkg = False
        name, _, _ = name.partition(u'.')

        if name in package_versions:
          # Determine the package version.
          command = u'/usr/sbin/pkgutil --pkg-info {0:s}'.format(package_name)
          logging.info(u'Running: "{0:s}"'.format(command))
          process = subprocess.Popen(
              command, stdout=subprocess.PIPE, shell=True)
          if process.returncode is None:
            package_info, _ = process.communicate()
          else:
            package_info = ''

          if process.returncode != 0:
            logging.error(u'Running: "{0:s}" failed.'.format(command))
            result = False
            continue

          location = None
          version = None
          volume = None
          for attribute in package_info.split('\n'):
            if attribute.startswith(u'location: '):
              _, _, location = attribute.rpartition(u'location: ')

            elif attribute.startswith(u'version: '):
              _, _, version = attribute.rpartition(u'version: ')

            elif attribute.startswith(u'volume: '):
              _, _, volume = attribute.rpartition(u'volume: ')

          if self._force_install:
            compare_result = -1
          elif name not in package_versions:
            compare_result = 1
          elif name in (u'pytsk', u'pytsk3'):
            # We cannot really tell by the version number that pytsk3 needs to
            # be updated, so just uninstall and update it any way.
            compare_result = -1
          else:
            version_tuple = version.split(u'.')
            compare_result = CompareVersions(
                version_tuple, package_versions[name])
            if compare_result >= 0:
              # The latest or newer version is already installed.
              del package_versions[name]

          if compare_result < 0:
            # Determine the files in the package.
            command = u'/usr/sbin/pkgutil --files {0:s}'.format(package_name)
            logging.info(u'Running: "{0:s}"'.format(command))
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, shell=True)
            if process.returncode is None:
              package_files, _ = process.communicate()
            else:
              package_files = u''

            if process.returncode != 0:
              logging.error(u'Running: "{0:s}" failed.'.format(command))
              result = False
              continue

            directories = []
            files = []
            for filename in package_files.split('\n'):
              if is_package_maker_pkg:
                filename = u'{0:s}{1:s}/{2:s}/{3:s}'.format(
                    volume, location, sub_name, filename)
              else:
                filename = u'{0:s}{1:s}'.format(location, filename)

              if os.path.isdir(filename):
                directories.append(filename)
              else:
                files.append(filename)

            logging.info(u'Removing: {0:s} {1:s}'.format(name, version))
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

            command = u'/usr/sbin/pkgutil --forget {0:s}'.format(
                package_name)
            exit_code = subprocess.call(command, shell=True)
            if exit_code != 0:
              logging.error(u'Running: "{0:s}" failed.'.format(command))
              result = False

    return result

  def _UninstallPackagesWindows(self, package_versions):
    """Uninstalls packages on Windows.

    Args:
      package_versions (dict[str, str]): versions per package.

    Returns:
      bool: True if the uninstall was successful.
    """
    connection = wmi.WMI()

    query = u'SELECT Name FROM Win32_Product'
    for product in connection.query(query):
      name = getattr(product, u'Name', u'')
      # Windows package names start with 'Python' or 'Python 2.7 '.
      if name.startswith(u'Python '):
        _, _, name = name.rpartition(u' ')
        if name.startswith(u'2.7 '):
          _, _, name = name.rpartition(u' ')

        name, _, version = name.rpartition(u'-')

        found_package = name in package_versions

        version_tuple = version.split(u'.')
        if self._force_install:
          compare_result = -1
        elif not found_package:
          compare_result = 1
        else:
          compare_result = CompareVersions(
              version_tuple, package_versions[name])
          if compare_result >= 0:
            # The latest or newer version is already installed.
            del package_versions[name]

        if not found_package and name.startswith(u'py'):
          # Remove libyal Python packages using the old naming convention.
          new_name = u'lib{0:s}-python'.format(name[2:])
          if new_name in package_versions:
            compare_result = -1

        if compare_result < 0:
          logging.info(u'Removing: {0:s} {1:s}'.format(name, version))
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
      logging.error(u'No packages found.')
      return False

    if self._download_only:
      return True

    if not self._UninstallPackages(package_versions):
      logging.error(u'Unable to uninstall packages.')
      return False

    return self._InstallPackages(package_filenames, package_versions)


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(description=(
      u'Installs the latest versions of project dependencies.'))

  argument_parser.add_argument(
      u'-c', u'--config', dest=u'config_path', action=u'store',
      metavar=u'CONFIG_PATH', default=None, help=(
          u'path of the directory containing the build configuration '
          u'files e.g. projects.ini.'))

  argument_parser.add_argument(
      u'--download-directory', u'--download_directory', action=u'store',
      metavar=u'DIRECTORY', dest=u'download_directory', type=str,
      default=u'build', help=u'The location of the download directory.')

  argument_parser.add_argument(
      '--download-only', u'--download_only', action='store_true',
      dest='download_only', default=False, help=(
          u'Only download the dependencies. The default behavior is to '
          u'download and update the dependencies.'))

  argument_parser.add_argument(
      '-e', '--exclude', action='store_true', dest='exclude_packages',
      default=False, help=(
          u'Excludes the package names instead of including them.'))

  argument_parser.add_argument(
      '-f', '--force', action='store_true', dest='force_install',
      default=False, help=(
          u'Force installation. This option removes existing versions '
          u'of installed dependencies. The default behavior is to only'
          u'install a dependency if not or an older version is installed.'))

  argument_parser.add_argument(
      '--machine-type', '--machine_type', action=u'store', metavar=u'TYPE',
      dest=u'machine_type', type=str, default=None, help=(
          u'Manually sets the machine type instead of using the value returned '
          u'by platform.machine(). Usage of this argument is not recommended '
          u'unless want to force the installation of one machine type e.g. '
          u'\'x86\' onto another \'amd64\'.'))

  argument_parser.add_argument(
      '--msi-targetdir', '--msi_targetdir', action=u'store', metavar=u'TYPE',
      dest=u'msi_targetdir', type=str, default=None, help=(
          u'Manually sets the MSI TARGETDIR property. Usage of this argument '
          u'is not recommended unless want to force the installation of the '
          u'MSIs into different directory than the system default.'))

  argument_parser.add_argument(
      u'--preset', dest=u'preset', action=u'store',
      metavar=u'PRESET_NAME', default=None, help=(
          u'name of the preset of project names to update. The default is to '
          u'build all project defined in the projects.ini configuration file. '
          u'The presets are defined in the preset.ini configuration file.'))

  argument_parser.add_argument(
      '-v', '--verbose', dest='verbose', action='store_true', default=False,
      help=u'have more verbose output.')

  argument_parser.add_argument(
      u'project_names', nargs=u'*', action=u'store', metavar=u'NAME',
      type=str, help=(
          u'Optional project names which should be updated if an update is '
          u'available. The corresponding package names are derived from '
          u'the projects.ini configuration file. If no value is provided '
          u'all available packages are updated.'))

  options = argument_parser.parse_args()

  config_path = options.config_path
  if not config_path:
    config_path = os.path.dirname(__file__)
    config_path = os.path.dirname(config_path)
    config_path = os.path.join(config_path, u'data')

  presets_file = os.path.join(config_path, u'presets.ini')
  if options.preset and not os.path.exists(presets_file):
    print(u'No such config file: {0:s}.'.format(presets_file))
    print(u'')
    return False

  projects_file = os.path.join(config_path, u'projects.ini')
  if not os.path.exists(projects_file):
    print(u'No such config file: {0:s}.'.format(projects_file))
    print(u'')
    return False

  logging.basicConfig(
      level=logging.INFO, format=u'[%(levelname)s] %(message)s')

  project_names = []
  if options.preset:
    with open(presets_file) as file_object:
      preset_definition_reader = presets.PresetDefinitionReader()
      for preset_definition in preset_definition_reader.Read(file_object):
        if preset_definition.name == options.preset:
          project_names = preset_definition.project_names
          break

    if not project_names:
      print(u'Undefined preset: {0:s}'.format(options.preset))
      print(u'')
      return False

  elif options.project_names:
    project_names = options.project_names

  dependency_updater = DependencyUpdater(
      download_directory=options.download_directory,
      download_only=options.download_only,
      exclude_packages=options.exclude_packages,
      force_install=options.force_install,
      msi_targetdir=options.msi_targetdir,
      preferred_machine_type=options.machine_type,
      verbose_output=options.verbose)

  project_definitions = {}
  with open(projects_file) as file_object:
    project_definition_reader = projects.ProjectDefinitionReader()
    for project_definition in project_definition_reader.Read(file_object):
      project_definitions[project_definition.name] = project_definition

  package_names = []
  for project_name in project_names:
    project_definition = project_definitions.get(project_name, None)
    if not project_definition:
      logging.error(u'Missing definition for project: {0:s}'.format(
          project_name))
      continue

    package_name = project_name
    if (dependency_updater.operating_system == u'Windows' and
        project_definition.msi_name):
      package_name = project_definition.msi_name

    package_names.append(package_name)

  return dependency_updater.UpdatePackages(package_names)


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
