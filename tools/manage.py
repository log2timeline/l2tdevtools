#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to manage the GIFT launchpad PPA and l2tbinaries."""

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import csv
import gzip
import io
import json
import logging
import os
import platform
import re
import sys
import zlib

from xml.etree import ElementTree

from l2tdevtools import versions
from l2tdevtools.download_helpers import interface


class COPRProjectManager(object):
  """Defines a COPR project manager."""

  _COPR_BASE_URL = 'https://copr.fedorainfracloud.org{0:s}'

  _COPR_URL = (
      'https://copr.fedorainfracloud.org/api_2/projects?group={name:s}&'
      'name={project:s}')

  _COPR_REPO_URL = (
      'https://copr-be.cloud.fedoraproject.org/results/%40{name:s}/'
      '{project:s}/fedora-{fedora_version:s}-i386')

  _PRIMARY_XML_XPATH = (
      './{http://linux.duke.edu/metadata/repo}data[@type="primary"]/'
      '{http://linux.duke.edu/metadata/repo}location')

  def __init__(self, name, distribution='28'):
    """Initializes a COPR manager.

    Args:
      name (str): name of the group.
      distribution (Optional[str]): name of the distribution.
    """
    super(COPRProjectManager, self).__init__()
    self._distribution = distribution
    self._download_helper = interface.DownloadHelper('')
    self._name = name

  def GetPackages(self, project):
    """Retrieves a list of packages of a specific project.

    Args:
      project (str): project name.

    Returns:
      dict[str, str]: package names and versions as values or None if
          the packages cannot be determined.
    """
    # TODO: do not use builds information, it is incomplete
    # instead use https://copr-be.cloud.fedoraproject.org/results/%40gift/
    # testing/fedora-26-x86_64/repodata/repomd.xml
    # to find primary.xml.gz or primary.sqlite.bz2

    kwargs = {
        'fedora_version': self._distribution,
        'name': self._name,
        'project': project}
    copr_repo_url = self._COPR_REPO_URL.format(**kwargs)

    download_url = '/'.join([copr_repo_url, 'repodata', 'repomd.xml'])
    page_content = self._download_helper.DownloadPageContent(download_url)
    if not page_content:
      logging.error('Unable to retrieve repomd.xml.')
      return None

    repomd_xml = ElementTree.fromstring(page_content)
    xml_elements = repomd_xml.findall(self._PRIMARY_XML_XPATH)
    if not xml_elements or not xml_elements[0].items():
      logging.error('Primary data type missing from repomd.xml.')
      return None

    href_value_tuple = xml_elements[0].items()[0]
    if not href_value_tuple[1]:
      logging.error('Primary data type missing from repomd.xml.')
      return None

    download_url = '/'.join([copr_repo_url, href_value_tuple[1]])
    page_content = self._download_helper.DownloadPageContent(
        download_url, encoding=None)
    if not page_content:
      _, _, download_url = download_url.rpartition('/')
      logging.error('Unable to retrieve primary.xml.gz.')
      return None

    with gzip.GzipFile(fileobj=io.BytesIO(page_content)) as file_object:
      page_content = file_object.read()

    primary_xml = ElementTree.fromstring(page_content)
    # Note explicitly checking xml.Element against None because of deprecation
    # warning.
    if primary_xml is None:
      logging.error('Packages missing from primary.xml.')
      return None

    packages = {}
    for project_xml in primary_xml:
      arch_xml = project_xml.find('{http://linux.duke.edu/metadata/common}arch')
      if arch_xml is None or arch_xml.text != 'src':
        continue

      package_name_xml = project_xml.find(
          '{http://linux.duke.edu/metadata/common}name')
      package_version_xml = project_xml.find(
          '{http://linux.duke.edu/metadata/common}version')
      if package_name_xml is None or package_version_xml is None:
        continue

      package_name = package_name_xml.text
      package_version = package_version_xml.attrib['ver']

      if not package_name or not package_version:
        continue

      if package_name in packages:
        package_version_tuple = package_version.split('.')
        version_tuple = packages[package_name].split('.')
        compare_result = versions.CompareVersions(
            package_version_tuple, version_tuple)
        if compare_result < 0:
          continue

      packages[package_name] = package_version

    return packages


class GithubRepoManager(object):
  """Defines a GitHub repository manager."""

  _GITHUB_REPO_API_URL = (
      'https://api.github.com/repos/log2timeline/l2tbinaries')

  _GITHUB_REPO_URL = (
      'https://github.com/log2timeline/l2tbinaries')

  def __init__(self):
    """Initializes a GitHub repository manager."""
    super(GithubRepoManager, self).__init__()
    self._download_helper = interface.DownloadHelper('')

  def _GetDownloadURL(self, sub_directory, track, use_api=False):
    """Retrieves the download URL.

    Args:
      sub_directory (str): machine type sub directory.
      track (str): track name.
      use_api (Optional[bool]): True if the API should be used.

    Returns:
      str: download URL or None if sub directory is missing.
    """
    if not sub_directory:
      return None

    if track == 'stable':
      branch = 'master'
    else:
      branch = track

    if use_api:
      download_url = '{0:s}/contents/{1:s}?ref={2:s}'.format(
          self._GITHUB_REPO_API_URL, sub_directory, branch)

    else:
      download_url = '{0:s}/tree/{1:s}/{2:s}'.format(
          self._GITHUB_REPO_URL, branch, sub_directory)

    return download_url

  def GetPackages(self, sub_directory, track, use_api=False):
    """Retrieves a list of packages of a specific sub directory.

    Args:
      sub_directory (str): machine type sub directory.
      track (str): track name.
      use_api (Optional[bool]): True if the API should be used.

    Returns:
      dict[str, str]: package names and versions as values or None if
          the packages cannot be determined.
    """
    if not sub_directory:
      logging.info('Missing machine type sub directory.')
      return None

    download_url = self._GetDownloadURL(sub_directory, track, use_api=use_api)
    if not download_url:
      logging.info('Missing download URL.')
      return None

    page_content = self._download_helper.DownloadPageContent(download_url)
    if not page_content:
      return None

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
        filename = directory_entry.get('name', None)
        if filename:
          filenames.append(filename)

    else:
      # The format of the download URL is:
      # <a class="js-navigation-open" title="{title}" id="{id}" href="{path}"
      expression_string = (
          '<a class="js-navigation-open" title="[^"]*" id="[^"]*" '
          'href="([^"]*)"')
      matches = re.findall(expression_string, page_content)

      for match in matches:
        _, _, filename = match.rpartition('/')
        filenames.append(filename)

    packages = {}
    for filename in filenames:
      if not filename:
        continue

      if filename.endswith('.dmg'):
        filename, _, _ = filename.rpartition('.dmg')

      elif filename.endswith('.msi'):
        if sub_directory == 'win32':
          filename, _, _ = filename.rpartition('.win32')
        elif sub_directory == 'win64':
          filename, _, _ = filename.rpartition('.win-amd64')

      else:
        continue

      name, _, version = filename.rpartition('-')
      packages[name] = version

    return packages


class LaunchpadPPAManager(object):
  """Defines a Launchpad PPA manager."""

  _LAUNCHPAD_URL = (
      'http://ppa.launchpad.net/{name:s}/{track:s}/ubuntu/dists'
      '/{distribution:s}/main/source/Sources.gz')

  def __init__(self, name, distribution='trusty'):
    """Initializes a Launchpad PPA manager.

    Args:
      name (str): name of the PPA.
      distribution (Optional[str]): name of the distribution.
    """
    super(LaunchpadPPAManager, self).__init__()
    self._distribution = distribution
    self._download_helper = interface.DownloadHelper('')
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
        'distribution': self._distribution,
        'name': self._name,
        'track': track}
    download_url = self._LAUNCHPAD_URL.format(**kwargs)

    ppa_sources = self._download_helper.DownloadPageContent(
        download_url, encoding=None)
    if not ppa_sources:
      logging.error('Unable to retrieve PPA sources list.')
      return None

    ppa_sources = zlib.decompress(ppa_sources, 16 + zlib.MAX_WBITS)

    try:
      ppa_sources = ppa_sources.decode('utf-8')
    except UnicodeDecodeError as exception:
      logging.error(
          'Unable to decode PPA sources list with error: {0!s}'.format(
              exception))
      return None

    packages = {}
    for line in ppa_sources.split('\n'):
      if line.startswith('Package: '):
        _, _, package = line.rpartition('Package: ')

      elif line.startswith('Version: '):
        _, _, version = line.rpartition('Version: ')
        version, _, _ = version.rpartition('-')

        packages[package] = version

    return packages


class OpenSuseBuildServiceManager(object):
  """Defines an OpenSuse build service manager object."""

  # http://download.opensuse.org/repositories/home:/joachimmetz:/testing/
  # Fedora_22/src/


class PyPIManager(object):
  """Defines a PyPI manager object."""

  _PYPI_URL = 'https://pypi.python.org/pypi/{package_name:s}'

  # TODO: move to projects.ini configuration.
  _PYPI_PACKAGE_NAMES = {
      'artifacts': 'artifacts',
      'astroid': 'astroid',
      'bencode': 'bencode',
      'binplist': 'binplist',
      'construct': 'construct',
      'dfdatetime': 'dfdatetime',
      'dfvfs': 'dfvfs',
      'dfwinreg': 'dfwinreg',
      'dpkt': 'dpkt',
      'efilter': 'efilter',
      'google-apputils': 'google-apputils',
      'hachoir-core': 'hachoir-core',
      'hachoir-metadata': 'hachoir-metadata',
      'hachoir-parser': 'hachoir-parser',
      'lazy-object-proxy': 'lazy-object-proxy',
      'libbde-python': 'libbde',
      'libcaes-python': 'libcaes',
      'libcreg-python': 'libcreg',
      'libesedb-python': 'libesedb',
      'libevt-python': 'libevt',
      'libevtx-python': 'libevtx',
      'libewf-python': 'libewf',
      'libexe-python': 'libexe',
      'libfsntfs-python': 'libfsntfs',
      'libfwps-python': 'libfwps',
      'libfwsi-python': 'libfwsi',
      'liblnk-python': 'liblnk',
      'libmsiecf-python': 'libmsiecf',
      'libolecf-python': 'libolecf',
      'libqcow-python': 'libqcow',
      'libregf-python': 'libregf',
      'libscca-python': 'libscca',
      'libsigscan-python': 'libsigscan',
      'libsmdev-python': 'libsmdev',
      'libsmraw-python': 'libsmraw',
      'libvhdi-python': 'libvhdi',
      'libvmdk-python': 'libvmdk',
      'libvshadow-python': 'libvshadow',
      'libvslvm-python': 'libvslvm',
      'logilab-common': 'logilab-common',
      'pefile': 'pefile',
      'pycrypto': 'pycrypto',
      'pylint': 'pylint',
      'pyparsing': 'pyparsing',
      'pysqlite': 'pysqlite',
      'python-dateutil': 'dateutil',
      'python-gflags': 'python-gflags',
      'pytsk3': 'pytsk3',
      'pytz': 'pytz',
      'PyYAML': 'PyYAML',
      'requests': 'requests',
      'six': 'six',
      'wrapt': 'wrapt',
      'XlsxWriter': 'XlsxWriter'}

  def __init__(self):
    """Initializes a PyPI manager object."""
    super(PyPIManager, self).__init__()
    self._download_helper = interface.DownloadHelper('')

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
      kwargs = {'package_name': package_name}
      download_url = self._PYPI_URL.format(**kwargs)

      page_content = self._download_helper.DownloadPageContent(download_url)
      if not page_content:
        logging.error('Unable to retrieve PyPI package: {0:s} page.'.format(
            package_name))
        continue

      try:
        page_content = page_content.decode('utf-8')
      except UnicodeDecodeError as exception:
        logging.error((
            'Unable to decode PyPI package: {0:s} page with error: '
            '{1:s}').format(package_name, exception))
        continue

      expression_string = (
          '<title>{0:s} ([^ ]*) : Python Package Index</title>'.format(
              package_name))
      matches = re.findall(expression_string, page_content)
      if not matches or len(matches) != 1:
        logging.warning(
            'Unable to determine PyPI package: {0:s} information.'.format(
                package_name))
        continue

      package_name = self._PYPI_PACKAGE_NAMES[package_name]
      packages[package_name] = matches

    return packages


class PackagesManager(object):
  """Manages packages across various repositories."""

  def __init__(self, distribution=None):
    """Initializes a packages manager.

    Args:
      distribution (Optional[str]): name of the distribution.
    """
    fedora_distribution = distribution or '28'
    ubuntu_distribution = distribution or 'trusty'

    super(PackagesManager, self).__init__()
    self._copr_project_manager = COPRProjectManager(
        'gift', distribution=fedora_distribution)
    self._distribution = distribution
    self._github_repo_manager = GithubRepoManager()
    self._launchpad_ppa_manager = LaunchpadPPAManager(
        'gift', distribution=ubuntu_distribution)
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
        continue

      new_version_tuple = packages[name].split('.')
      version_tuple = version.split('.')

      if new_version_tuple > version_tuple:
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
      if not directory_entry.endswith('.src.rpm'):
        continue

      name, _, _ = directory_entry.rpartition('-')
      name, _, version = name.rpartition('-')

      reference_packages[name] = version

    packages = self._copr_project_manager.GetPackages(project)
    return self._ComparePackages(reference_packages, packages)

  def CompareDirectoryWithCSV(self, reference_directory, csv_file):
    """Compares a directory containing source packages with a CSV file.

    Args:
      reference_directory (str): path of the reference directory that contains
          dpkg source packages.
      csv_file (str): path of the CSV file.

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
      # in the source packages that use the naming convention:
      # package-version-#.tar.gz
      # package-version-#.zip
      if (not directory_entry.endswith('.tar.gz') and
          not directory_entry.endswith('.zip')):
        continue

      if (directory_entry.endswith('.debian.tar.gz') or
          directory_entry.endswith('.orig.tar.gz') or
          directory_entry.endswith('-1.tar.gz')):
        continue

      name, _, _ = directory_entry.rpartition('.')
      if name.endswith('.tar'):
        name, _, _ = name.rpartition('.')
      name, _, version = name.rpartition('-')

      if (name.endswith('-alpha') or
          name.endswith('-beta') or
          name.endswith('-experimental')):
        name, _, _ = name.rpartition('-')

      reference_packages[name] = version

    packages = {}
    with open(csv_file, 'r') as file_object:
      for row in csv.DictReader(file_object):
        packages[row['project']] = row['version']

    return self._ComparePackages(reference_packages, packages)

  def CompareDirectoryWithGithubRepo(
      self, reference_directory, sub_directory, track):
    """Compares a directory containing msi or dmg packages with a GitHub repo.

    Args:
      reference_directory (str): path of the reference directory that contains
          msi or dmg packages.
      sub_directory (str): name of the machine type sub directory.
      track (str): name of the track.

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
      if directory_entry.endswith('.dmg'):
        directory_entry, _, _ = directory_entry.rpartition('.dmg')

      elif directory_entry.endswith('.msi'):
        if sub_directory == 'win32':
          directory_entry, _, _ = directory_entry.rpartition('.win32')
        elif sub_directory == 'win64':
          directory_entry, _, _ = directory_entry.rpartition('.win-amd64')

      else:
        continue

      name, _, version = directory_entry.rpartition('-')
      reference_packages[name] = version

    packages = self._github_repo_manager.GetPackages(sub_directory, track)
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
      # package_version-#ppa1~distribution_source.changes
      name_suffix = 'ppa1~{0:s}_source.changes'.format(self._distribution)
      if not directory_entry.endswith(name_suffix):
        continue

      name, _, _ = directory_entry.rpartition('-')
      name, _, version = name.rpartition('_')

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

  def CompareGithubRepos(self, sub_directory, reference_track, track):
    """Compares two GitHub repos PPA tracks.

    Args:
      sub_directory (str): name of the machine type sub directory.
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
    reference_packages = self._github_repo_manager.GetPackages(
        sub_directory, reference_track)
    packages = self._github_repo_manager.GetPackages(sub_directory, track)

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
      if not directory_entry.endswith('.tar.gz'):
        continue

      directory_entry, _, _ = directory_entry.rpartition('.tar.gz')
      name, _, version = directory_entry.rpartition('-')

      if (name.endswith('-alpha') or name.endswith('-beta') or
          name.endswith('-experimental')):
        name, _, _ = name.rpartition('-')

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
      str: machine type sub directory or None if system configuration is not
          supported.
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

    if operating_system == 'Darwin':
      # TODO: determine OSX version.
      if cpu_architecture != 'x86_64':
        logging.error('CPU architecture: {0:s} not supported.'.format(
            cpu_architecture))
        return None

      sub_directory = 'macos'

    elif operating_system == 'Linux':
      # pylint: disable=deprecated-method
      linux_name, linux_version, _ = platform.linux_distribution()
      logging.error('Linux: {0:s} {1:s} not supported.'.format(
          linux_name, linux_version))

      if linux_name == 'Ubuntu':
        wiki_url = (
            'https://github.com/log2timeline/plaso/wiki/Dependencies---Ubuntu'
            '#prepackaged-dependencies')
        logging.error(
            'Use the gift PPA instead. For more info see: {0:s}'.format(
                wiki_url))

      return None

    elif operating_system == 'Windows':
      if cpu_architecture == 'x86':
        sub_directory = 'win32'

      elif cpu_architecture == 'amd64':
        sub_directory = 'win64'

      else:
        logging.error('CPU architecture: {0:s} not supported.'.format(
            cpu_architecture))
        return None

    else:
      logging.error('Operating system: {0:s} not supported.'.format(
          operating_system))
      return None

    return sub_directory


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  actions = frozenset([
      'copr-diff-dev', 'copr-diff-stable', 'copr-diff-testing', 'csv-diff',
      'l2tbinaries-diff-dev', 'l2tbinaries-diff-stable',
      'l2tbinaries-diff-testing', 'launchpad-diff-dev', 'launchpad-diff-stable',
      'launchpad-diff-testing', 'pypi-diff'])

  argument_parser = argparse.ArgumentParser(description=(
      'Manages the GIFT copr, launchpad PPA and l2tbinaries.'))

  argument_parser.add_argument(
      'action', choices=sorted(actions), action='store',
      metavar='ACTION', default=None, help='The action.')

  argument_parser.add_argument(
      '--build-directory', '--build_directory', action='store',
      metavar='DIRECTORY', dest='build_directory', type=str,
      default='build', help='The location of the build directory.')

  argument_parser.add_argument(
      '--csv-file', '--csv_file', action='store', metavar='FILE',
      dest='csv_file', type=str, default='', help=(
          'The location of the CSV file.'))

  argument_parser.add_argument(
      '--distribution', action='store', metavar='NAME', dest='distribution',
      type=str, default=None, help='The name or version of the distribution.')

  argument_parser.add_argument(
      '--machine-type', '--machine_type', action='store', metavar='TYPE',
      dest='machine_type', type=str, default=None, help=(
          'Manually sets the machine type instead of using the value returned '
          'by platform.machine(). Usage of this argument is not recommended '
          'unless want to force the installation of one machine type e.g. '
          '\'x86\' onto another \'amd64\'.'))

  options = argument_parser.parse_args()

  if not options.action:
    print('Missing action.')
    print('')
    argument_parser.print_help()
    print('')
    return False

  # TODO: add action to upload files to PPA.
  # TODO: add action to copy files between PPA tracks.
  # TODO: add pypi support.

  packages_manager = PackagesManager(distribution=options.distribution)

  action_tuple = options.action.split('-')

  if action_tuple[0] == 'copr' and action_tuple[1] == 'diff':
    track = action_tuple[2]

    if track == 'testing':
      reference_directory = options.build_directory

      new_packages, new_versions = (
          packages_manager.CompareDirectoryWithCOPRProject(
              reference_directory, track))

      diff_header = (
          'Difference between: {0:s} and COPR project: {1:s}'.format(
              reference_directory, track))

    else:
      if track == 'dev':
        reference_track = 'testing'
      else:
        reference_track = 'dev'

      new_packages, new_versions = packages_manager.CompareCOPRProjects(
          reference_track, track)

      diff_header = (
          'Difference between COPR project: {0:s} and {1:s}'.format(
              reference_track, track))

  elif action_tuple[0] == 'csv' and action_tuple[1] == 'diff':
    reference_directory = options.build_directory

    new_packages, new_versions = (
        packages_manager.CompareDirectoryWithCSV(
            reference_directory, options.csv_file))

    diff_header = (
        'Difference between: {0:s} and CSV'.format(reference_directory))

  elif action_tuple[0] == 'l2tbinaries' and action_tuple[1] == 'diff':
    sub_directory = packages_manager.GetMachineTypeSubDirectory(
        preferred_machine_type=options.machine_type)

    if track == 'testing':
      reference_directory = options.build_directory

      new_packages, new_versions = (
          packages_manager.CompareDirectoryWithGithubRepo(
              reference_directory, sub_directory, track))

      diff_header = (
          'Difference between: {0:s} and testing for: {1:s}'.format(
              reference_directory, sub_directory))

    else:
      if track == 'dev':
        reference_track = 'testing'
      else:
        reference_track = 'dev'

      new_packages, new_versions = packages_manager.CompareGithubRepos(
          sub_directory, reference_track, track)

      diff_header = (
          'Difference between l2tbinaries tracks: {0:s} and {1:s} for: '
          '{2:s}').format(reference_track, track, sub_directory)

  elif action_tuple[0] == 'launchpad' and action_tuple[1] == 'diff':
    track = action_tuple[2]

    if track == 'testing':
      reference_directory = options.build_directory

      new_packages, new_versions = (
          packages_manager.CompareDirectoryWithLaunchpadPPATrack(
              reference_directory, track))

      diff_header = (
          'Difference between: {0:s} and Launchpad track: {1:s}'.format(
              reference_directory, track))

    else:
      if track == 'dev':
        reference_track = 'testing'
      else:
        reference_track = 'dev'

      new_packages, new_versions = packages_manager.CompareLaunchpadPPATracks(
          reference_track, track)

      diff_header = (
          'Difference between Launchpad tracks: {0:s} and {1:s}'.format(
              reference_track, track))

  # elif action_tuple[0] == 'osb' and action_tuple[1] == 'diff':

  elif action_tuple[0] == 'pypi' and action_tuple[1] == 'diff':
    reference_directory = options.build_directory

    new_packages, new_versions = (
        packages_manager.CompareDirectoryWithPyPI(reference_directory))

    diff_header = (
        'Difference between: {0:s} and release'.format(reference_directory))

  if action_tuple[1] == 'diff':
    print(diff_header)
    print('')

    print('New packages:')
    for package in sorted(new_packages.keys()):
      print('  {0:s}'.format(package))
    print('')

    print('New versions:')
    for package in sorted(new_versions.keys()):
      print('  {0:s}'.format(package))
    print('')

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
