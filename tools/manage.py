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
import zlib

from l2tdevtools import download_helper


class COPRProjectManager(object):
  """Defines a COPR project manager."""

  _COPR_BASE_URL = u'https://copr.fedorainfracloud.org{0:s}'

  _COPR_URL = (
      u'https://copr.fedorainfracloud.org/api_2/projects?group={name:s}&'
      u'name={project:s}')

  def __init__(self, name):
    """Initializes the COPR manager.

    Args:
      name (str): name of the group.
    """
    super(COPRProjectManager, self).__init__()
    self._download_helper = download_helper.DownloadHelper(u'')
    self._name = name

  def GetPackages(self, project):
    """Retrieves a list of packages of a specific project.

    Args:
      project (str): project name.

    Returns:
      dict[str, str]: package names and versions as values or None if
          the packages cannot be determined.
    """
    kwargs = {
        u'name': self._name,
        u'project': project}
    download_url = self._COPR_URL.format(**kwargs)

    page_content = self._download_helper.DownloadPageContent(download_url)
    if not page_content:
      logging.error(u'Unable to retrieve project information page content.')
      return

    project_information = json.loads(page_content)
    if not project_information:
      logging.error(u'Unable to retrieve project information.')
      return

    projects = project_information.get(u'projects', None)
    if len(projects) != 1:
      return

    links = projects[0].get(u'_links', None)
    if not links:
      return

    builds = links.get(u'builds', None)
    if not builds:
      return

    builds_href = builds.get(u'href', None)
    if not builds_href:
      return

    download_url = self._COPR_BASE_URL.format(builds_href)

    page_content = self._download_helper.DownloadPageContent(download_url)
    if not page_content:
      logging.error(u'Unable to retrieve builds information page content.')
      return

    builds_information = json.loads(page_content)
    if not builds_information:
      logging.error(u'Unable to retrieve builds information.')
      return

    builds = builds_information.get(u'builds', None)
    if not builds:
      return

    packages = {}
    for build_information in builds:
      build = build_information.get(u'build', None)
      if not build:
        continue

      package_name = build.get(u'package_name', None)
      package_version = build.get(u'package_version', None)
      if not package_name or not package_version:
        continue

      package_version, _, _ = package_version.rpartition(u'-')
      # TODO: improve version check.
      if package_name in packages and packages[package_name] > package_version:
        continue

      packages[package_name] = package_version

    return packages


class GithubRepoManager(object):
  """Defines a github reposistory manager."""

  _GITHUB_REPO_API_URL = (
      u'https://api.github.com/repos/log2timeline/l2tbinaries')

  _GITHUB_REPO_URL = (
      u'https://github.com/log2timeline/l2tbinaries')

  def __init__(self):
    """Initializes the github reposistory manager."""
    super(GithubRepoManager, self).__init__()
    self._download_helper = download_helper.DownloadHelper(u'')

  def _GetDownloadURL(self, sub_directory, use_api=False):
    """Retrieves the download URL.

    Args:
      sub_directory (str): machine type sub directory.
      use_api (Optional[bool]): True if the API should be used.

    Returns:
      str: download URL or None.
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
    """Retrieves a list of packages of a specific sub directory.

    Args:
      sub_directory (str): machine type sub directory.
      use_api (Optional[bool]): True if the API should be used.

    Returns:
      dict[str, str]: package names and versions as values or None if
          the packages cannot be determined.
    """
    if not sub_directory:
      logging.info(u'Missing machine type sub directory.')
      return

    download_url = self._GetDownloadURL(sub_directory, use_api=use_api)
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

    packages = {}
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

      name, _, version = filename.rpartition(u'-')
      packages[name] = version

    return packages


class LaunchpadPPAManager(object):
  """Defines a Launchpad PPA manager."""

  _LAUNCHPAD_URL = (
      u'http://ppa.launchpad.net/{name:s}/{track:s}/ubuntu/dists'
      u'/trusty/main/source/Sources.gz')

  def __init__(self, name):
    """Initializes the Launchpad PPA manager.

    Args:
      name (str): name of the PPA.
    """
    super(LaunchpadPPAManager, self).__init__()
    self._download_helper = download_helper.DownloadHelper(u'')
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
      track (str): PPA track name.

    Returns:
      dict[str, str]: package names and versions as values or None if
          the packages cannot be determined.
    """
    kwargs = {
        u'name': self._name,
        u'track': track}
    download_url = self._LAUNCHPAD_URL.format(**kwargs)

    ppa_sources = self._download_helper.DownloadPageContent(download_url)
    if not ppa_sources:
      logging.error(u'Unable to retrieve PPA sources list.')
      return

    ppa_sources = zlib.decompress(ppa_sources, 16 + zlib.MAX_WBITS)

    try:
      ppa_sources = ppa_sources.decode(u'utf-8')
    except UnicodeDecodeError as exception:
      logging.error(
          u'Unable to decode PPA sources list with error: {0:s}'.format(
              exception))
      return

    packages = {}
    for line in ppa_sources.split(u'\n'):
      if line.startswith(u'Package: '):
        _, _, package = line.rpartition(u'Package: ')

      elif line.startswith(u'Version: '):
        _, _, version = line.rpartition(u'Version: ')
        version, _, _ = version.rpartition(u'-')

        packages[package] = version

    return packages


class OpenSuseBuildServiceManager(object):
  """Defines an OpenSuse build service manager object."""

  # http://download.opensuse.org/repositories/home:/joachimmetz:/testing/
  # Fedora_22/src/


class PyPIManager(object):
  """Defines a PyPI manager object."""

  _PYPI_URL = u'https://pypi.python.org/pypi/{package_name:s}'

  # TODO: move to projects.ini configuration.
  _PYPI_PACKAGE_NAMES = {
      u'artifacts': u'artifacts',
      u'astroid': u'astroid',
      u'bencode': u'bencode',
      u'binplist': u'binplist',
      u'construct': u'construct',
      u'dfdatetime': u'dfdatetime',
      u'dfvfs': u'dfvfs',
      u'dfwinreg': u'dfwinreg',
      u'dpkt': u'dpkt',
      u'efilter': u'efilter',
      u'google-apputils': u'google-apputils',
      u'hachoir-core': u'hachoir-core',
      u'hachoir-metadata': u'hachoir-metadata',
      u'hachoir-parser': u'hachoir-parser',
      u'lazy-object-proxy': u'lazy-object-proxy',
      u'libbde-python': u'libbde',
      u'libcaes-python': u'libcaes',
      u'libcreg-python': u'libcreg',
      u'libesedb-python': u'libesedb',
      u'libevt-python': u'libevt',
      u'libevtx-python': u'libevtx',
      u'libewf-python': u'libewf',
      u'libexe-python': u'libexe',
      u'libfsntfs-python': u'libfsntfs',
      u'libfwps-python': u'libfwps',
      u'libfwsi-python': u'libfwsi',
      u'liblnk-python': u'liblnk',
      u'libmsiecf-python': u'libmsiecf',
      u'libolecf-python': u'libolecf',
      u'libqcow-python': u'libqcow',
      u'libregf-python': u'libregf',
      u'libscca-python': u'libscca',
      u'libsigscan-python': u'libsigscan',
      u'libsmdev-python': u'libsmdev',
      u'libsmraw-python': u'libsmraw',
      u'libvhdi-python': u'libvhdi',
      u'libvmdk-python': u'libvmdk',
      u'libvshadow-python': u'libvshadow',
      u'libvslvm-python': u'libvslvm',
      u'logilab-common': u'logilab-common',
      u'pefile': u'pefile',
      u'pycrypto': u'pycrypto',
      u'pylint': u'pylint',
      u'pyparsing': u'pyparsing',
      u'pysqlite': u'pysqlite',
      u'python-dateutil': u'dateutil',
      u'python-gflags': u'python-gflags',
      u'pytsk3': u'pytsk3',
      u'pytz': u'pytz',
      u'PyYAML': u'PyYAML',
      u'requests': u'requests',
      u'six': u'six',
      u'wrapt': u'wrapt',
      u'XlsxWriter': u'XlsxWriter'}

  def __init__(self):
    """Initializes the PyPI manager object."""
    super(PyPIManager, self).__init__()
    self._download_helper = download_helper.DownloadHelper(u'')

  def CopyPackages(self):
    """Copies packages."""
    # TODO: implement:
    # send post to https://launchpad.net/~gift/+archive/ubuntu/testing
    #              /+copy-packages
    return

  def GetPackages(self):
    """Retrieves a list of packages.

    Returns:
      dict[str, str]: package names and versions as values or None if
          the packages cannot be determined.
    """
    packages = {}
    for package_name in iter(self._PYPI_PACKAGE_NAMES.keys()):
      kwargs = {u'package_name': package_name}
      download_url = self._PYPI_URL.format(**kwargs)

      page_content = self._download_helper.DownloadPageContent(download_url)
      if not page_content:
        logging.error(u'Unable to retrieve PyPI package: {0:s} page.'.format(
            package_name))
        continue

      try:
        page_content = page_content.decode(u'utf-8')
      except UnicodeDecodeError as exception:
        logging.error((
            u'Unable to decode PyPI package: {0:s} page with error: '
            u'{1:s}').format(package_name, exception))
        continue

      expression_string = (
          u'<title>{0:s} ([^ ]*) : Python Package Index</title>'.format(
              package_name))
      matches = re.findall(expression_string, page_content)
      if not matches or len(matches) != 1:
        logging.warning(
            u'Unable to determine PyPI package: {0:s} information.'.format(
                package_name))
        continue

      package_name = self._PYPI_PACKAGE_NAMES[package_name]
      packages[package_name] = matches

    return packages


class BinariesManager(object):
  """Defines the binaries manager."""

  def __init__(self):
    """Initializes the binaries manager object."""
    super(BinariesManager, self).__init__()
    self._copr_project_manager = COPRProjectManager(u'gift')
    self._github_repo_manager = GithubRepoManager()
    self._launchpad_ppa_manager = LaunchpadPPAManager(u'gift')
    self._pypi_manager = PyPIManager()

  def _ComparePackages(self, reference_packages, packages):
    """Compares the packages.

    Args:
      reference_packages (dict[str, str]): reference package names and versions.
      packages (dict[str, str]): package names and versions.

    Returns:
      tuple: containing:

        dict[str, str]: new package names and versions. New packages are those
            that are present in the reference packages but not in the packages.
        dict[str, str]: newer existing package names and versions. Newer
            existing packages are those that have a newer version in the
            reference packages.
    """
    new_packages = {}
    new_versions = {}
    for name, version in iter(reference_packages.items()):
      if not packages or name not in packages:
        new_packages[name] = version
      elif version != packages[name]:
        new_versions[name] = version

    return new_packages, new_versions

  def CompareDirectoryWithCOPRProject(self, reference_directory, project):
    """Compares a directory containing source rpm packages with a COPR project.

    Args:
      reference_directory (str): path of the reference directory that contains
          dpkg source packages.
      project (str): name of the COPR project.

    Returns:
      tuple: containing:

        dict[str, str]: new package names and versions. New packages are those
            that are present in the reference directory but not in the project.
        dict[str, str]: newer existing package names and versions. Newer
            existing packages are those that have a newer version in the
            reference directory.
    """
    reference_packages = {}
    for directory_entry in os.listdir(reference_directory):
      # The directory contains various files and we are only interested
      # in the source RPM packages that use the naming convention:
      # package-version-#.src.rpm
      if not directory_entry.endswith(u'.src.rpm'):
        continue

      name, _, _ = directory_entry.rpartition(u'-')
      name, _, version = name.rpartition(u'-')

      reference_packages[name] = version

    packages = self._copr_project_manager.GetPackages(project)
    return self._ComparePackages(reference_packages, packages)

  def CompareDirectoryWithGithubRepo(self, reference_directory, sub_directory):
    """Compares a directory containing msi or dmg packages with a github repo.

    Args:
      reference_directory (str): path of the reference directory that contains
          msi or dmg packages.
      sub_directory (str): name of the machine type sub directory.

    Returns:
      tuple: containing:

        dict[str, str]: new package names and versions. New packages are those
            that are present in the reference directory but not in the sub
            directory.
        dict[str, str]: newer existing package names and versions. Newer
            existing packages are those that have a newer version in the
            reference directory.
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

      name, _, version = directory_entry.rpartition(u'-')
      reference_packages[name] = version

    packages = self._github_repo_manager.GetPackages(sub_directory)
    return self._ComparePackages(reference_packages, packages)

  def CompareDirectoryWithLaunchpadPPATrack(
      self, reference_directory, track):
    """Compares a directory containing dpkg packages with a Launchpad PPA track.

    Args:
      reference_directory (str): path of the reference directory that contains
          dpkg source packages.
      track (str): name of the track.

    Returns:
      tuple: containing:

        dict[str, str]: new package names and versions. New packages are those
            that are present in the reference directory but not in the track.
        dict[str, str]: newer existing package names and versions. Newer
            existing packages are those that have a newer version in the
            reference directory.
    """
    reference_packages = {}
    for directory_entry in os.listdir(reference_directory):
      # The directory contains various files and we are only interested
      # in the source dpkg packages that use the naming convention:
      # package_version-#ppa1~trusty_source.changes
      if not directory_entry.endswith(u'ppa1~trusty_source.changes'):
        continue

      name, _, _ = directory_entry.rpartition(u'-')
      name, _, version = name.rpartition(u'_')

      reference_packages[name] = version

    packages = self._launchpad_ppa_manager.GetPackages(track)
    return self._ComparePackages(reference_packages, packages)

  def CompareCOPRProjects(self, reference_project, project):
    """Compares two COPR projects.

    Args:
      reference_project (str): name of the reference project.
      project (str): name of the project.

    Returns:
      tuple: containing:

        dict[str, str]: new package names and versions. New packages are those
            that are present in the reference project but not in the project.
        dict[str, str]: newer existing package names and versions. Newer
            existing packages are those that have a newer version in the
            reference project.
    """
    reference_packages = self._copr_project_manager.GetPackages(
        reference_project)
    packages = self._copr_project_manager.GetPackages(project)

    return self._ComparePackages(reference_packages, packages)

  def CompareLaunchpadPPATracks(self, reference_track, track):
    """Compares two Launchpad PPA tracks.

    Args:
      reference_track (str): name of the reference track.
      track (str): name of the track.

    Returns:
      tuple: containing:

        dict[str, str]: new package names and versions. New packages are those
            that are present in the reference track but not in the track.
        dict[str, str]: newer existing package names and versions. Newer
            existing packages are those that have a newer version in the
            reference track.
    """
    reference_packages = self._launchpad_ppa_manager.GetPackages(
        reference_track)
    packages = self._launchpad_ppa_manager.GetPackages(track)

    return self._ComparePackages(reference_packages, packages)

  def CompareDirectoryWithPyPI(self, reference_directory):
    """Compares a directory containing .tar.gz packages with PyPI.

    Args:
      reference_directory (str): path of the reference directory that
          contains msi or dmg packages.

    Returns:
      tuple: containing:

        dict[str, str]: new package names and versions. New packages are those
            that are present in the reference directory but not on PyPI.
        dict[str, str]: newer existing package names and versions. Newer
            existing packages are those that have a newer version in the
            reference directory.
    """
    reference_packages = {}
    for directory_entry in os.listdir(reference_directory):
      if not directory_entry.endswith(u'.tar.gz'):
        continue

      directory_entry, _, _ = directory_entry.rpartition(u'.tar.gz')
      name, _, version = directory_entry.rpartition(u'-')

      if (name.endswith(u'-alpha') or name.endswith(u'-beta') or
          name.endswith(u'-experimental')):
        name, _, _ = name.rpartition(u'-')

      reference_packages[name] = version

    packages = self._pypi_manager.GetPackages()
    return self._ComparePackages(reference_packages, packages)

  def GetMachineTypeSubDirectory(
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
      # TODO: determine OSX version.
      if cpu_architecture != u'x86_64':
        logging.error(u'CPU architecture: {0:s} not supported.'.format(
            cpu_architecture))
        return

      sub_directory = u'macos'

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
    bool: True if successful or False if not.
  """
  actions = frozenset([
      u'copr-diff-dev', u'copr-diff-stable', u'copr-diff-testing',
      u'l2tbinaries-diff', u'launchpad-diff-dev', u'launchpad-diff-stable',
      u'launchpad-diff-testing', u'pypi-diff'])

  argument_parser = argparse.ArgumentParser(description=(
      u'Manages the GIFT copr, launchpad PPA and l2tbinaries.'))

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

  if action_tuple[0] == u'copr' and action_tuple[1] == u'diff':
    track = action_tuple[2]

    if track == u'testing':
      reference_directory = options.build_directory

      new_packages, new_versions = (
          binaries_manager.CompareDirectoryWithCOPRProject(
              reference_directory, track))

      diff_header = (
          u'Difference between: {0:s} and COPR project: {1:s}'.format(
              reference_directory, track))

    else:
      if track == u'dev':
        reference_track = u'testing'
      else:
        reference_track = u'dev'

      new_packages, new_versions = binaries_manager.CompareCOPRProjects(
          reference_track, track)

      diff_header = (
          u'Difference between COPR project: {0:s} and {1:s}'.format(
              reference_track, track))

  elif action_tuple[0] == u'l2tbinaries' and action_tuple[1] == u'diff':
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
          binaries_manager.CompareDirectoryWithLaunchpadPPATrack(
              reference_directory, track))

      diff_header = (
          u'Difference between: {0:s} and Launchpad track: {1:s}'.format(
              reference_directory, track))

    else:
      if track == u'dev':
        reference_track = u'testing'
      else:
        reference_track = u'dev'

      new_packages, new_versions = binaries_manager.CompareLaunchpadPPATracks(
          reference_track, track)

      diff_header = (
          u'Difference between Launchpad tracks: {0:s} and {1:s}'.format(
              reference_track, track))

  # elif action_tuple[0] == u'osb' and action_tuple[1] == u'diff':

  elif action_tuple[0] == u'pypi' and action_tuple[1] == u'diff':
    reference_directory = options.build_directory

    new_packages, new_versions = (
        binaries_manager.CompareDirectoryWithPyPI(reference_directory))

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
