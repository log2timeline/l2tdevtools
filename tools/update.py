#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to update prebuilt versions of the projects."""

import argparse
import glob
import logging
import os
import platform
import re
import subprocess
import sys

from l2tdevtools import download_helper


if platform.system() == u'Windows':
  import wmi


def CompareVersions(first_version_list, second_version_list):
  """Compares two lists containing version parts.

  Note that the version parts can contain alpha numeric characters.

  Args:
    first_version_list: the first list of version parts.
    second_version_list: the second list of version parts.

  Returns:
    1 if the first is larger than the second, -1 if the first is smaller than
    the second, or 0 if the first and second are equal.
  """
  first_version_list_length = len(first_version_list)
  second_version_list_length = len(second_version_list)

  for index in range(0, first_version_list_length):
    if index >= second_version_list_length:
      return 1

    if first_version_list[index] > second_version_list[index]:
      return 1
    elif first_version_list[index] < second_version_list[index]:
      return -1

  if first_version_list_length < second_version_list_length:
    return -1

  return 0


# TODO: merge this class with download_helper.GoogleDriveDownloadHelper.
class GoogleDriveDownloadHelper(download_helper.DownloadHelper):
  """Class that helps in downloading from Google Drive."""

  # pylint: disable=abstract-method
  # Prevent pylint from remarking that GetDownloadUrl and GetProjectIdentifier
  # are not overwritten.

  def GetPackageDownloadUrls(self, google_drive_url):
    """Retrieves the package downloads URL for a given URL.

    Args:
      google_drive_url: the Google Drive URL.

    Returns:
      A list of package download URLs.
    """
    page_content = self.DownloadPageContent(google_drive_url)
    if not page_content:
      return

    # The format of the project download URL is:
    # /host/{random string}/3rd%20party/{sub directory}/{filename}
    expression_string = u'/host/[^/]+/3rd%20party/[^/">]+/[^">]+'
    matches = re.findall(expression_string, page_content)

    for match_index in range(0, len(matches)):
      matches[match_index] = u'https://googledrive.com{0:s}'.format(
          matches[match_index])

    return matches

  def DownloadPackage(self, download_url):
    """Downloads the package for a given URL.

    Args:
      download_url: the download URL.

    Returns:
      The filename if successful also if the file was already downloaded
      or None on error.
    """
    return self.DownloadFile(download_url)


class DependencyUpdater(object):
  """Class that helps in updating dependencies."""

  _GOOGLE_DRIVE_URL = (
      u'https://googledrive.com/host/0B30H7z4S52FleW5vUHBnblJfcjg')

  def __init__(
      self, download_directory=u'build', force_install=False,
      preferred_machine_type=None):
    """Initializes the dependency updater.

    Args:
      download_directory: optional download directory. The default is 'build'
                          to match the build directory of the build script.
      force_install: optional boolean value to indicate installation (update)
                     should be forced. The default is False.
      preferred_machine_type: optional preferred machine type. The default
                              is None, which will auto-detect the current
                              machine type.
    """
    super(DependencyUpdater, self).__init__()
    self._download_directory = download_directory
    self._download_helper = GoogleDriveDownloadHelper()
    self._force_install = force_install
    self._linux_name = None
    self._noarch_sub_directory = None
    self._operating_system = platform.system()

    if preferred_machine_type:
      self._preferred_machine_type = preferred_machine_type.lower()
    else:
      self._preferred_machine_type = None

  def _GetDownloadUrl(self):
    """Retrieves the download URL.

    Returns:
      The download URL or None.
    """
    if self._preferred_machine_type:
      cpu_architecture = self._preferred_machine_type
    else:
      cpu_architecture = platform.machine().lower()

    sub_directory = None

    if self._operating_system == u'Darwin':
      # TODO: determine OSX version
      if cpu_architecture != u'x86_64':
        logging.error(u'CPU architecture: {0:s} not supported.'.format(
            cpu_architecture))
        return

      # Note that the sub directory should be URL encoded.
      sub_directory = u'macosx%2010.10'

    elif self._operating_system == u'Linux':
      linux_name, linux_version, _ = platform.linux_distribution()
      if linux_name == u'Fedora' and linux_version == u'20':
        if cpu_architecture != u'x86_64':
          logging.error(u'CPU architecture: {0:s} not supported.'.format(
              cpu_architecture))
          return

        sub_directory = u'fedora20-x86_64'
        self._noarch_sub_directory = u'fedora20-noarch'

      elif linux_name == u'Ubuntu':
        wiki_url = (
            u'https://github.com/log2timeline/plaso/wiki/Dependencies---Ubuntu'
            u'#prepackaged-dependencies')
        logging.warning((
            u'Ubuntu is no longer supported by this script. Use the gift PPA '
            u'instead. For more info see: {0:s}').format(wiki_url))
        return

      else:
        logging.error(u'Linux variant: {0:s} {1:s} not supported.'.format(
            self._linux_name, linux_version))
        return

    elif self._operating_system == u'Windows':
      if cpu_architecture == u'x86':
        sub_directory = u'win32-vs2008'

      elif cpu_architecture == u'amd64':
        sub_directory = u'win-amd64-vs2010'

      else:
        logging.error(u'CPU architecture: {0:s} not supported.'.format(
            cpu_architecture))
        return

    else:
      logging.error(u'Operating system: {0:s} not supported.'.format(
          self._operating_system))
      return

    return u'{0:s}/3rd%20party/{1:s}'.format(
        self._GOOGLE_DRIVE_URL, sub_directory)

  def _GetPackageFilenamesAndVersions(self):
    """Determines the package filenames and versions.

    Args:
      A tuple of two dictionaries one containing the package filenames
      another the package versions per package name.
    """
    package_urls = self._GetPackageUrls()
    if not package_urls:
      return None, None

    if not os.path.exists(self._download_directory):
      os.mkdir(self._download_directory)

    os.chdir(self._download_directory)

    package_filenames = {}
    package_versions = {}
    for package_url in package_urls:
      _, _, package_filename = package_url.rpartition(u'/')
      if package_filename.endswith(u'.deb'):
        name, _, version = package_filename.partition(u'_')

        # Ignore development and tools DEB packages.
        if name.endswith(u'-dev') or name.endswith(u'-tools'):
          continue

        if name.endswith(u'-python'):
          package_prefix = name
          name, _, _ = name.partition(u'-')
        else:
          package_prefix = u'{0:s}_'.format(name)
        version, _, _ = version.partition(u'-')
        package_suffix = u'.deb'

      elif package_filename.endswith(u'.dmg'):
        name, _, version = package_filename.partition(u'-')
        version, _, _ = version.partition(u'.dmg')
        package_prefix = name
        package_suffix = u'.dmg'

      elif package_filename.endswith(u'.msi'):
        name, _, version = package_filename.partition(u'-')
        version, _, _ = version.partition(u'.win')
        package_prefix = name
        package_suffix = u'.msi'

      elif package_filename.endswith(u'.rpm'):
        name, _, version = package_filename.partition(u'-')

        # Ignore debuginfo, devel and tools RPM packages.
        if (version.startswith(u'debuginfo') or version.startswith(u'devel') or
            version.startswith(u'tools')):
          continue

        # Ignore the sleuthkit tools RPM package.
        if name == u'sleuthkit' and not version.startswith(u'libs'):
          continue

        package_prefix, _, version = version.partition(u'-')
        version, _, _ = version.partition(u'-')
        package_prefix = u'{0:s}-{1:s}'.format(name, package_prefix)
        package_suffix = u'.rpm'

      else:
        # Ignore all other file exensions.
        continue

      version = version.split(u'.')
      if name == u'pytsk':
        last_part = version.pop()
        version.extend(last_part.split(u'-'))

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
        _ = self._download_helper.DownloadPackage(package_url)

    os.chdir(u'..')

    return package_filenames, package_versions

  def _GetPackageUrls(self):
    """Retrieves a list of package URLs.

    The package URL are determined based on the files in an architecture
    specific sub directories of the download URL.

    Returns:
      A list of package URLs or None.
    """
    download_url = self._GetDownloadUrl()
    if not download_url:
      return

    package_urls = self._download_helper.GetPackageDownloadUrls(download_url)

    if self._noarch_sub_directory:
      noarch_package_urls = self._download_helper.GetPackageDownloadUrls(
          u'{0:s}/3rd%20party/{1:s}'.format(
              self._GOOGLE_DRIVE_URL, self._noarch_sub_directory))

      package_urls.extend(noarch_package_urls)

    # TODO: do something with noarch_package_urls.

    return package_urls

  def _InstallPackages(self, package_filenames, package_versions):
    """Installs packages.

    Args:
      package_filenames: a dictionary containing the package filenames per
                         package name.
      package_versions: a dictionary containing the package version per
                         package name.

    Returns:
      A boolean value indicating the install was successful.
    """
    if self._operating_system == u'Darwin':
      return self._InstallPackagesMacOSX(
          package_filenames, package_versions)

    elif self._operating_system == u'Linux':
      if self._linux_name == u'Fedora':
        return self._InstallPackagesFedoraLinux(
            package_filenames, package_versions)

    elif self._operating_system == u'Windows':
      return self._InstallPackagesWindows(
          package_filenames, package_versions)

    return False

  def _InstallPackagesFedoraLinux(
      self, unused_package_filenames, unused_package_versions):
    """Installs packages on Fedora Linux.

    Args:
      package_filenames: a dictionary containing the package filenames per
                         package name.
      package_versions: a dictionary containing the package version per
                         package name.

    Returns:
      A boolean value indicating the install was successful.
    """
    result = True
    # TODO: move these to a separate file?
    dependencies = [
        u'ipython',
        u'libyaml'
        u'python-dateutil',
        u'pyparsing',
        u'pytz',
        u'PyYAML',
        u'protobuf-python']

    command = u'sudo yum install {0:s}'.format(u' '.join(dependencies))
    logging.info(u'Running: "{0:s}"'.format(command))
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      result = False

    command = u'sudo rpm -Fvh {0:s}/*'.format(self._download_directory)
    logging.info(u'Running: "{0:s}"'.format(command))
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      result = False

    return result

  def _InstallPackagesMacOSX(self, package_filenames, package_versions):
    """Installs packages on Mac OS X.

    Args:
      package_filenames: a dictionary containing the package filenames per
                         package name.
      package_versions: a dictionary containing the package version per
                         package name.

    Returns:
      A boolean value indicating the install was successful.
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
      package_filenames: a dictionary containing the package filenames per
                         package name.
      package_versions: a dictionary containing the package version per
                         package name.

    Returns:
      A boolean value indicating the install was successful.
    """
    result = True
    for name, version in package_versions.iteritems():
      # TODO: add RunAs ?
      package_filename = package_filenames[name]
      command = u'msiexec.exe /i {0:s} /q'.format(os.path.join(
          self._download_directory, package_filename))
      logging.info(u'Installing: {0:s} {1:s}'.format(name, u'.'.join(version)))
      exit_code = subprocess.call(command, shell=False)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        result = False

    return result

  def _UninstallPackages(self, package_versions):
    """Uninstalls packages if necessary.

    It is preferred that the system package manager handles this, however not
    every operating system seems to have a package manager capable to do so.

    Args:
      package_versions: a dictionary containing the package version per
                         package name.

    Returns:
      A boolean value indicating the uninstall was successful.
    """
    if self._operating_system == u'Darwin':
      return self._UninstallPackagesMacOSX(package_versions)

    elif self._operating_system == u'Windows':
      return self._UninstallPackagesWindows(package_versions)

    return True

  def _UninstallPackagesMacOSX(self, package_versions):
    """Uninstalls packages on Mac OS X.

    Args:
      package_versions: a dictionary containing the package version per
                         package name.

    Returns:
      A boolean value indicating the uninstall was successful.
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

      if (package_name.startswith(u'com.github.libyal.') or
          package_name.startswith(u'com.github.log2timeline.') or
          package_name.startswith(u'com.github.sleuthkit.') or
          package_name.startswith(u'com.google.code.p.') or
          package_name.startswith(u'org.samba.') or
          package_name.startswith(u'org.python.pypi.') or
          package_name.startswith(u'net.sourceforge.projects.')):

        if package_name.startswith(u'com.github.libyal.'):
          name = package_name[18:]

        elif package_name.startswith(u'com.github.log2timeline.'):
          name = package_name[24:]

        elif package_name.startswith(u'com.github.sleuthkit.'):
          name = package_name[21:]

        elif package_name.startswith(u'com.google.code.p.'):
          name = package_name[18:]

        elif package_name.startswith(u'org.samba.'):
          name = package_name[10:]

        elif package_name.startswith(u'org.python.pypi.'):
          name = package_name[16:]

        elif package_name.startswith(u'net.sourceforge.projects.'):
          name = package_name[25:]

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

          version = version.split(u'.')
          if self._force_install:
            compare_result = -1
          elif name not in package_versions:
            compare_result = 1
          elif name == u'pytsk':
            # We cannot really tell by the version number that pytsk needs to
            # be updated, so just uninstall and update it any way.
            compare_result = -1
          else:
            compare_result = CompareVersions(version, package_versions[name])
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
              package_files = ''

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
      package_versions: a dictionary containing the package version per
                         package name.

    Returns:
      A boolean value indicating the uninstall was successful.
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

        name, _, version = name.partition(u'-')

        version = version.split(u'.')
        if self._force_install:
          compare_result = -1
        elif name not in package_versions:
          compare_result = 1
        elif name == u'pytsk':
          # We cannot really tell by the version number that pytsk needs to
          # be updated, so just uninstall and update it any way.
          compare_result = -1
        else:
          compare_result = CompareVersions(version, package_versions[name])
          if compare_result >= 0:
            # The latest or newer version is already installed.
            del package_versions[name]

        if compare_result < 0:
          logging.info(u'Removing: {0:s} {1:s}'.format(
              name, u'.'.join(version)))
          product.Uninstall()

    return True

  def UpdatePackages(self, package_names):
    """Updates packages.

    Args:
      package_names: a list of package names that should be updated
                     if an update is available. An empty list represents
                     all available packges.

    Returns:
      A boolean value indicating the update was successful.
    """
    package_filenames, package_versions = self._GetPackageFilenamesAndVersions()
    if not package_filenames:
      return False

    if package_names:
      # Since the dictionary is going to change a list of the keys is needed.
      for package_name in package_filenames.keys():
        if package_name not in package_names:
          del package_filenames[package_name]

      # Since the dictionary is going to change a list of the keys is needed.
      for package_name in package_versions.keys():
        if package_name not in package_names:
          del package_versions[package_name]

    if not self._UninstallPackages(package_versions):
      return False

    return self._InstallPackages(package_filenames, package_versions)


def Main():
  argument_parser = argparse.ArgumentParser(description=(
      u'Installs the latest versions of project dependencies.'))

  argument_parser.add_argument(
      u'package_names', nargs=u'*', action=u'store', metavar=u'NAME',
      type=unicode, help=(
          u'Optional package names which should be updated if an update is '
          u'available. If no value is provided all available packages are '
          u'updated.'))

  argument_parser.add_argument(
      u'--download-directory', u'--download_directory', action=u'store',
      metavar=u'DIRECTORY', dest=u'download_directory', type=unicode,
      default=u'build', help=u'The location of the the download directory.')

  argument_parser.add_argument(
      '-f', '--force', action='store_true', dest='force_install',
      default=False, help=(
          u'Force installation. This option removes existing versions '
          u'of installed dependencies. The default behavior is to only'
          u'install a dependency if not or an older version is installed.'))

  argument_parser.add_argument(
      '--machine-type', '--machine_type', action=u'store', metavar=u'TYPE',
      dest=u'machine_type', type=unicode, default=None, help=(
          u'Manually sets the machine type instead of using the value returned '
          u'by platform.machine(). Usage of this argument is not recommended '
          u'unless want to force the installation of one machine type e.g. '
          u'\'x86\' onto another \'amd64\'.'))

  options = argument_parser.parse_args()

  logging.basicConfig(
      level=logging.INFO, format=u'[%(levelname)s] %(message)s')

  dependency_updater = DependencyUpdater(
      download_directory=options.download_directory,
      force_install=options.force_install,
      preferred_machine_type=options.machine_type)

  return dependency_updater.UpdatePackages(options.package_names)


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
