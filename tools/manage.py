#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to manage the GIFT launchpad PPA and l2tbinaries."""

from __future__ import print_function
import argparse
import json
import logging
import os
import platform
import re
import sys

from l2tdevtools import download_helper


class GithubRepoManager(object):
  """Defines a github reposistory manager object."""

  _GITHUB_REPO_API_URL = (
      u'https://api.github.com/repos/log2timeline/l2tbinaries')

  _GITHUB_REPO_URL = (
      u'https://github.com/log2timeline/l2tbinaries')

  def __init__(self):
    """Initializes the github reposistory manager object."""
    super(GithubRepoManager, self).__init__()
    self._download_helper = download_helper.DownloadHelper()

  def _GetDownloadUrl(self, sub_directory, use_api=False):
    """Retrieves the download URL.

    Args:
      sub_directory: a string containing the machine type sub directory.
      use_api: optional boolean value to indicate if the API should be used.
               The default is False.

    Returns:
      The download URL or None.
    """
    if not sub_directory:
      return

    if use_api:
      download_url = u'{0:s}/contents/{1:s}'.format(
          self._GITHUB_REPO_API_URL, sub_directory)

    else:
      download_url = u'{0:s}/tree/master/{1:s}'.format(
          self._GITHUB_REPO_URL, sub_directory)

    return download_url

  def GetPackages(self, sub_directory, use_api=False):
    """Retrieves a list of packages of a specific PPA track.

    Args:
      sub_directory: a string containing the machine type sub directory.
      use_api: optional boolean value to indicate if the API should be used.
               The default is False.

    Returns:
      A dictionary object containing the project names as keys and
      versions as values or None if the projects cannot be determined.
    """
    if not sub_directory:
      logging.info(u'Missing machine type sub directory.')
      return

    download_url = self._GetDownloadUrl(sub_directory, use_api=use_api)
    if not download_url:
      logging.info(u'Missing download URL.')
      return

    page_content = self._download_helper.DownloadPageContent(download_url)
    if not page_content:
      return

    filenames = []
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
        filename = directory_entry.get(u'name', None)
        if filename:
          filenames.append(filename)

    else:
      # The format of the download URL is:
      # <a href="{path}" class="js-directory-link"
      # <a href="{path}" class="js-directory-link js-navigation-open"
      expression_string = u'<a href="([^"]*)" class="js-directory-link'
      matches = re.findall(expression_string, page_content)

      for match in matches:
        _, _, filename = match.rpartition(u'/')
        filenames.append(filename)

    projects = {}
    for filename in filenames:
      if not filename:
        continue

      if filename.endswith(u'.dmg'):
        filename, _, _ = filename.rpartition(u'.dmg')

      elif filename.endswith(u'.msi'):
        if sub_directory == u'win32':
          filename, _, _ = filename.rpartition(u'.win32')
        elif sub_directory == u'win64':
          filename, _, _ = filename.rpartition(u'.win-amd64')

      else:
        continue

      if filename.startswith(u'pefile') or filename.startswith(u'pystsk'):
        project, _, version = filename.partition(u'-')
      else:
        project, _, version = filename.rpartition(u'-')

      projects[project] = version

    return projects


class LaunchpadPPAManager(object):
  """Defines a Launchpad PPA manager object."""

  _LAUNCHPAD_URL = (
      u'http://ppa.launchpad.net/{name:s}/{track:s}/ubuntu/dists'
      u'/trusty/main/source/Sources')

  def __init__(self, name):
    """Initializes the Launchpad PPA manager object.

    Args:
      name: a string containing the name of the PPA.
    """
    super(LaunchpadPPAManager, self).__init__()
    self._download_helper = download_helper.DownloadHelper()
    self._name = name

  def CopyPackages(self):
    """Copies packages."""
    # TODO: implement:
    # send post to https://launchpad.net/~gift/+archive/ubuntu/testing
    #              /+copy-packages
    return

  def GetPackages(self, track):
    """Retrieves a list of packages of a specific PPA track.

    Args:
      track: a string containing the PPA track name.

    Returns:
      A dictionary object containing the project names as keys and
      versions as values or None if the projects cannot be determined.
    """
    kwargs = {
        u'name': self._name,
        u'track': track}
    download_url = self._LAUNCHPAD_URL.format(**kwargs)

    ppa_sources = self._download_helper.DownloadPageContent(download_url)
    if not ppa_sources:
      logging.error(u'Unable to retrieve PPA sources list.')
      return

    try:
      ppa_sources = ppa_sources.decode(u'utf-8')
    except UnicodeDecodeError as exception:
      logging.error(
          u'Unable to decode PPA sources list with error: {0:s}'.format(
              exception))
      return

    projects = {}
    for line in ppa_sources.split(u'\n'):
      if line.startswith(u'Package: '):
        _, _, project = line.rpartition(u'Package: ')

      elif line.startswith(u'Version: '):
        _, _, version = line.rpartition(u'Version: ')
        version, _, _ = version.rpartition(u'-')

        projects[project] = version

    return projects


class OpenSuseBuildServiceManager(object):
  """Defines an OpenSuse build service manager object."""

  # http://download.opensuse.org/repositories/home:/joachimmetz:/testing/
  # Fedora_22/src/


class PyPIManager(object):
  """Defines a PyPI manager object."""

  _PYPI_URL = u'https://pypi.python.org/pypi/{package_name:s}'

  _PACKAGE_NAMES = [
      u'artifacts',
      u'dfvfs',
      u'dfwinreg',
      u'libbde-python',
      u'libcaes-python',
      u'libcreg-python',
      u'libesedb-python',
      u'libevt-python',
      u'libevtx-python',
      u'libewf-python',
      u'libexe-python',
      u'libfsntfs-python',
      u'libfwps-python',
      u'libfwsi-python',
      u'liblnk-python',
      u'libmsiecf-python',
      u'libolecf-python',
      u'libqcow-python',
      u'libregf-python',
      u'libscca-python',
      u'libsigscan-python',
      u'libsmdev-python',
      u'libsmraw-python',
      u'libvhdi-python',
      u'libvmdk-python',
      u'libvshadow-python',
      u'libvslvm-python',
      u'pytsk3']

  def __init__(self):
    """Initializes the PyPI manager object."""
    super(PyPIManager, self).__init__()
    self._download_helper = download_helper.DownloadHelper()

  def CopyPackages(self):
    """Copies packages."""
    # TODO: implement:
    # send post to https://launchpad.net/~gift/+archive/ubuntu/testing
    #              /+copy-packages
    return

  def GetPackages(self):
    """Retrieves a list of packages.

    Returns:
      A dictionary object containing the project names as keys and
      versions as values or None if the projects cannot be determined.
    """
    projects = {}
    for package_name in self._PACKAGE_NAMES:
      kwargs = {u'package_name': package_name}
      download_url = self._PYPI_URL.format(**kwargs)

      page_content = self._download_helper.DownloadPageContent(download_url)
      if not page_content:
        logging.error(u'Unable to retrieve PyPI package: {0:s} page.'.format(
            package_name))
        return

      try:
        page_content = page_content.decode(u'utf-8')
      except UnicodeDecodeError as exception:
        logging.error((
            u'Unable to decode PyPI package: {0:s} page with error: '
            u'{1:s}').format(package_name, exception))
        return

      expression_string = u'<title>{0:s} ([^ ]*) : Python Package Index</title>'
      matches = re.findall(expression_string, page_content)
      if not matches or len(matches) != 1:
        logging.warning(
            u'Unable to determine PyPI package: {0:s} information.'.format(
                package_name))
        continue

      projects[package_name] = matches

    return projects


class BinariesManager(object):
  """Defines the binaries manager."""

  def __init__(self):
    """Initializes the binaries manager object."""
    super(BinariesManager, self).__init__()
    self._github_repo_manager = GithubRepoManager()
    self._launchpad_ppa_manager = LaunchpadPPAManager(u'gift')

  def _ComparePackages(self, reference_packages, packages):
    """Compares the packages.

    Args:
      reference_packages: a dictionary containing the reference package names
                          and versions.
      packages: a dictionary containing the package names and versions.

    Returns:
      A tuple containing a dictionary of the new packages, those packages that
      are present in the reference packages but not in the packages, and new
      version, those packages that have a newer version in the reference
      packages.
    """
    new_packages = {}
    new_versions = {}
    for name, version in iter(reference_packages.items()):
      if name not in packages:
        new_packages[name] = version
      elif version != packages[name]:
        new_versions[name] = version

    return new_packages, new_versions

  def CompareDirectoryWithGithubRepo(self, reference_directory, sub_directory):
    """Compares a directory containing msi or dmg packages with a github repo.

    Args:
      reference_directory: a string containing the path of the reference
                           directory that contains msi or dmg packages.
      sub_directory: a string containing the name of the machine type sub
                     directory.

    Returns:
      A tuple containing a dictionary of the new packages, those packages that
      are present in the reference directory but not in the track, and new
      version, those packages that have a newer version in the reference
      directory.
    """
    reference_packages = {}
    for directory_entry in os.listdir(reference_directory):
      if directory_entry.endswith(u'.dmg'):
        directory_entry, _, _ = directory_entry.rpartition(u'.dmg')

      elif directory_entry.endswith(u'.msi'):
        if sub_directory == u'win32':
          directory_entry, _, _ = directory_entry.rpartition(u'.win32')
        elif sub_directory == u'win64':
          directory_entry, _, _ = directory_entry.rpartition(u'.win-amd64')

      else:
        continue

      if (directory_entry.startswith(u'pefile') or
          directory_entry.startswith(u'pystsk')):
        name, _, version = directory_entry.partition(u'-')
      else:
        name, _, version = directory_entry.rpartition(u'-')

      reference_packages[name] = version

    packages = self._github_repo_manager.GetPackages(sub_directory)
    return self._ComparePackages(reference_packages, packages)

  def CompareDirectoryWithPPAReleaseTrack(self, reference_directory, track):
    """Compares a directory containing dpkg packages with a PPA release track.

    Args:
      reference_directory: a string containing the path of the reference
                           directory that contains dpkg source packages.
      track: a string containing the name of the track.

    Returns:
      A tuple containing a dictionary of the new packages, those packages that
      are present in the reference directory but not in the track, and new
      version, those packages that have a newer version in the reference
      directory.
    """
    reference_packages = {}
    for directory_entry in os.listdir(reference_directory):
      # The directory contains various files and we are only interested
      # in the source dpkg packges that use the naming convention:
      # package_version-#ppa1~trusty_source.changes
      if not directory_entry.endswith(u'ppa1~trusty_source.changes'):
        continue

      name, _, _ = directory_entry.rpartition(u'-')
      name, _, version = name.rpartition(u'_')

      reference_packages[name] = version

    packages = self._launchpad_ppa_manager.GetPackages(track)
    return self._ComparePackages(reference_packages, packages)

  def ComparePPAReleaseTracks(self, reference_track, track):
    """Compares two PPA release tracks.

    Args:
      reference_track: a string containing the name of the reference track.
      track: a string containing the name of the track.

    Returns:
      A tuple containing a dictionary of the new packages, those packages that
      are present in the reference track but not in the track, and new
      version, those packages that have a newer version in the reference track.
    """
    reference_packages = self._launchpad_ppa_manager.GetPackages(
        reference_track)
    packages = self._launchpad_ppa_manager.GetPackages(track)

    return self._ComparePackages(reference_packages, packages)

  def CompareDirectoryWithPyPI(self, reference_directory, sub_directory):
    """Compares a directory containing .tar.gz packages with a github repo.

    Args:
      reference_directory: a string containing the path of the reference
                           directory that contains msi or dmg packages.
      sub_directory: a string containing the name of the machine type sub
                     directory.

    Returns:
      A tuple containing a dictionary of the new packages, those packages that
      are present in the reference directory but not in the track, and new
      version, those packages that have a newer version in the reference
      directory.
    """
    reference_packages = {}
    for directory_entry in os.listdir(reference_directory):
      if directory_entry.endswith(u'.dmg'):
        directory_entry, _, _ = directory_entry.rpartition(u'.dmg')

      elif directory_entry.endswith(u'.msi'):
        if sub_directory == u'win32':
          directory_entry, _, _ = directory_entry.rpartition(u'.win32')
        elif sub_directory == u'win64':
          directory_entry, _, _ = directory_entry.rpartition(u'.win-amd64')

      else:
        continue

      if (directory_entry.startswith(u'pefile') or
          directory_entry.startswith(u'pystsk')):
        name, _, version = directory_entry.partition(u'-')
      else:
        name, _, version = directory_entry.rpartition(u'-')

      reference_packages[name] = version

    packages = self._github_repo_manager.GetPackages(sub_directory)
    return self._ComparePackages(reference_packages, packages)

  def GetMachineTypeSubDirectory(
      self, preferred_machine_type=None, preferred_operating_system=None):
    """Retrieves the machine type sub directory.

    Args:
      preferred_machine_type: optional preferred machine type. The default
                              is None, which will auto-detect the current
                              machine type.
      preferred_operating_system: optional preferred operating system. The
                                  default is None, which will auto-detect
                                  the current operating system.

    Returns:
      The machine type sub directory or None.
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
      # TODO: determine OSX version.
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


def Main():
  """The main program function.

  Returns:
    A boolean containing True if successful or False if not.
  """
  actions = frozenset([
      u'l2tbinaries-diff', u'launchpad-diff-dev', u'launchpad-diff-stable',
      u'launchpad-diff-testing', u'pypi-diff'])

  argument_parser = argparse.ArgumentParser(description=(
      u'Manages the GIFT launchpad PPA and l2tbinaries.'))

  argument_parser.add_argument(
      u'action', choices=sorted(actions), action=u'store',
      metavar=u'ACTION', default=None, help=u'The action.')

  argument_parser.add_argument(
      u'--build-directory', u'--build_directory', action=u'store',
      metavar=u'DIRECTORY', dest=u'build_directory', type=str,
      default=u'build', help=u'The location of the build directory.')

  argument_parser.add_argument(
      '--machine-type', '--machine_type', action=u'store', metavar=u'TYPE',
      dest=u'machine_type', type=unicode, default=None, help=(
          u'Manually sets the machine type instead of using the value returned '
          u'by platform.machine(). Usage of this argument is not recommended '
          u'unless want to force the installation of one machine type e.g. '
          u'\'x86\' onto another \'amd64\'.'))

  options = argument_parser.parse_args()

  if not options.action:
    print(u'Missing action.')
    print(u'')
    argument_parser.print_help()
    print(u'')
    return False

  # TODO: add action to upload files to PPA.
  # TODO: add action to copy files between PPA tracks.
  # TODO: add l2tbinaries support.
  # TODO: add pypi support.

  binaries_manager = BinariesManager()

  action_tuple = options.action.split(u'-')

  if action_tuple[0] == u'l2tbinaries' and action_tuple[1] == u'diff':
    sub_directory = binaries_manager.GetMachineTypeSubDirectory(
        preferred_machine_type=options.machine_type)

    reference_directory = options.build_directory

    # TODO: compare from l2tbinaries git repo.
    new_packages, new_versions = (
        binaries_manager.CompareDirectoryWithGithubRepo(
            reference_directory, sub_directory))

    diff_header = (
        u'Difference between: {0:s} and release'.format(reference_directory))

  elif action_tuple[0] == u'launchpad' and action_tuple[1] == u'diff':
    track = action_tuple[2]

    if track == u'testing':
      reference_directory = options.build_directory

      new_packages, new_versions = (
          binaries_manager.CompareDirectoryWithPPAReleaseTrack(
              reference_directory, track))

      diff_header = (
          u'Difference between: {0:s} and release track: {1:s}'.format(
              reference_directory, track))

    else:
      if track == u'dev':
        reference_track = u'testing'
      else:
        reference_track = u'dev'

      new_packages, new_versions = binaries_manager.ComparePPAReleaseTracks(
          reference_track, track)

      diff_header = (
          u'Difference between release tracks: {0:s} and {1:s}'.format(
              reference_track, track))

  # elif action_tuple[0] == u'osb' and action_tuple[1] == u'diff':

  elif action_tuple[0] == u'pypi' and action_tuple[1] == u'diff':
    sub_directory = binaries_manager.GetMachineTypeSubDirectory(
        preferred_machine_type=options.machine_type)

    reference_directory = options.build_directory

    new_packages, new_versions = (
        binaries_manager.CompareDirectoryWithPyPI(
            reference_directory, sub_directory))

    diff_header = (
        u'Difference between: {0:s} and release'.format(reference_directory))

  if action_tuple[1] == u'diff':
    print(diff_header)
    print(u'')

    print(u'New packages:')
    for package in sorted(new_packages.keys()):
      print(u'  {0:s}'.format(package))
    print(u'')

    print(u'New versions:')
    for package in sorted(new_versions.keys()):
      print(u'  {0:s}'.format(package))
    print(u'')

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
