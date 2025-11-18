#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to update prebuilt versions of the projects."""

import argparse
import glob
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


class PackageDownload(object):
  """Information about a package download.

  Attributes:
    filename (str): name of the package file.
    name (str): name of the package.
    url (str): download URL of the package file.
    version (str): version of the package.
  """

  def __init__(self, name, version, filename, url):
    """Initializes a package download.

    Args:
      name (str): name of the package.
      version (str): version of the package.
      filename (str): name of the package file.
      url (str): download URL of the package file.
    """
    super(PackageDownload, self).__init__()
    self.filename = filename
    self.name = name
    self.url = url
    self.version = version


class GithubRepoDownloadHelper(interface.DownloadHelper):
  """Helps in downloading from a GitHub repository."""

  _GITHUB_REPO_API_URL = (
      'https://api.github.com/repos/log2timeline/l2tbinaries')

  _GITHUB_REPO_URL = (
      'https://github.com/log2timeline/l2tbinaries')

  _SUPPORTED_PYTHON_VERSIONS = frozenset([(3, 12), (3, 14)])

  def __init__(self, download_url, branch='main'):
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

    if operating_system != 'Windows':
      logging.error('Operating system: {0:s} not supported.'.format(
          operating_system))
      return None

    if (sys.version_info[0], sys.version_info[1]) not in (
        self._SUPPORTED_PYTHON_VERSIONS):
      logging.error('Python version: {0:d}.{1:d} not supported.'.format(
          sys.version_info[0], sys.version_info[1]))
      return None

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
      # <script type="application/json" data-target="react-app.embeddedData">
      # {"payload":{$JSON}}</script>
      expression_string = (
          '<script type="application/json" '
          'data-target="react-app.embeddedData">({"payload":{.*}})</script>')
      matches = re.findall(expression_string, page_content)

      if len(matches) == 1:
        json_dict = json.loads(matches[0])
        payload = json_dict.get('payload', {})
        tree = payload.get('tree', {})
        for item in tree.get('items', []):
          item_path = item.get('path', None)
          download_url = (
              'https://github.com/log2timeline/l2tbinaries/raw/{0:s}/'
              '{1:s}').format(self._branch, item_path)
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
      'stable': 'main',
      'staging': 'staging',
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

  # Some projects have different module names than their project names.
  _MODULE_ALIASES = {
      'flor': 'Flor',
      'lz4': 'python-lz4',
      'redis': 'redis-py',
      'snappy': 'python-snappy',
      'zstd': 'python-zstd'}

  # Some projects have different wheel names in l2tbinaries than defined
  # in their project definitions.
  _WHEEL_ALIASES = {
      # TODO: remove after l2tbinaries Python 3.14 upgrade.
      'bencode.py': 'bencode_py',
      # TODO: remove after l2tbinaries Python 3.14 upgrade.
      'PyYAML': 'pyyaml',
      # TODO: remove after l2tbinaries Python 3.14 upgrade.
      'XlsxWriter': 'xlsxwriter'}

  def __init__(
      self, download_directory='build', download_only=False,
      download_track='stable', exclude_packages=False, force_install=False,
      preferred_machine_type=None, preferred_operating_system=None,
      verbose_output=False):
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
      preferred_machine_type (Optional[str]): preferred machine type, where
          None, which will auto-detect the current machine type.
      preferred_operating_system (Optional[str]): preferred operating system,
          where None, which will auto-detect the current operating system.
      verbose_output (Optional[bool]): True more verbose output should be
          provided.
    """
    branch = self._GIT_BRANCH_PER_TRACK.get(download_track, 'main')

    super(DependencyUpdater, self).__init__()
    self._download_directory = download_directory
    self._download_helper = GithubRepoDownloadHelper(
        self._DOWNLOAD_URL, branch=branch)
    self._download_only = download_only
    self._download_track = download_track
    self._exclude_packages = exclude_packages
    self._force_install = force_install
    self._verbose_output = verbose_output

    if preferred_operating_system:
      self.operating_system = preferred_operating_system
    else:
      self.operating_system = platform.system()

    if preferred_machine_type:
      self._preferred_machine_type = preferred_machine_type.lower()
    else:
      self._preferred_machine_type = None

  def _GetAvailableWheelPackages(self):
    """Determines the wheel packages available for download.

    Returns:
      list[PackageDownload]: packages available for download.
    """
    python_version_indicator = 'cp{0:d}{1:d}'.format(
        sys.version_info[0], sys.version_info[1])

    # The API is rate limited, so we scrape the web page instead.
    package_urls = self._download_helper.GetPackageDownloadURLs(
        preferred_machine_type=self._preferred_machine_type,
        preferred_operating_system=self.operating_system)
    if not package_urls:
      logging.error('Unable to determine package download URLs.')
      return []

    # Use a dictionary so we can more efficiently set a newer version of
    # a package that was set previously.
    available_packages = {}

    package_versions = {}
    for package_url in package_urls:
      _, _, package_filename = package_url.rpartition('/')
      package_filename = package_filename.lower()

      if not package_filename.endswith('.whl'):
        # Ignore all other file extensions.
        continue

      (package_name, package_version, python_tags,
       _, _) = package_filename[:-4].split('-')

      if python_tags not in (python_version_indicator, 'py2.py3', 'py3'):
        # Ignore packages that are for different versions of Python.
        continue

      version = package_version.split('.')

      if package_name not in package_versions:
        compare_result = 1
      else:
        compare_result = versions.CompareVersions(
            version, package_versions[package_name])

      if compare_result > 0:
        package_versions[package_name] = version

        package_download = PackageDownload(
            package_name, version, package_filename, package_url)
        available_packages[package_name] = package_download

    return available_packages.values()

  def _GetWheelPackageFilenamesAndVersions(
      self, project_definitions, available_packages,
      user_defined_wheel_package_names):
    """Determines the wheel package filenames and versions.

    Args:
      project_definitions (dist[str, ProjectDefinition]): project definitions
          per name.
      available_packages (list[PackageDownload]): packages available for
          download.
      user_defined_wheel_package_names (list[str]): names of the wheels of
          packages that should be updated if an update is available. These
          package names are derived from the user specified names of projects.
          An empty list represents all available packages.

    Returns:
      tuple: containing:
          dict[str, str]: filenames per package.
          dict[str, str]: versions per package.
    """
    project_definition_per_package_name = {}
    for project_name, project_definition in project_definitions.items():
      package_name = getattr(
          project_definition, 'wheel_name', None) or project_name
      package_name = package_name.lower()
      project_definition_per_package_name[package_name] = project_definition

    package_filenames = {}
    package_versions = {}

    for package_download in available_packages:
      package_name = package_download.name
      package_filename = package_download.filename
      package_download_path = os.path.join(
          self._download_directory, package_filename)

      # Ignore package names if user defined.
      if user_defined_wheel_package_names:
        in_package_names = package_name in user_defined_wheel_package_names

        alternate_name = self._WHEEL_ALIASES.get(package_name, None)
        if alternate_name:
          if ((self._exclude_packages and in_package_names) or
              (not self._exclude_packages and not in_package_names)):
            in_package_names = alternate_name in user_defined_wheel_package_names

        if ((self._exclude_packages and in_package_names) or
            (not self._exclude_packages and not in_package_names)):
          logging.info('Skipping: {0:s} because it was excluded'.format(
              package_name))
          continue

      # Remove previous versions of a package.
      filenames_glob = '{0:s}*{1:s}'.format(package_name, package_filename[:-4])
      filenames = glob.glob(os.path.join(
          self._download_directory, filenames_glob))
      for filename in filenames:
        if filename != package_download_path and os.path.isfile(filename):
          logging.info('Removing: {0:s}'.format(filename))
          os.remove(filename)

      project_definition = project_definition_per_package_name.get(
          package_name, None)
      if not project_definition:
        alternate_name = self._WHEEL_ALIASES.get(package_name, None)
        if alternate_name:
          project_definition = project_definitions.get(alternate_name, None)

      if not project_definition:
        logging.error('Missing project definition for package: {0:s}'.format(
            package_name))
        continue

      if not os.path.exists(package_download_path):
        logging.info('Downloading: {0:s}'.format(package_filename))
        os.chdir(self._download_directory)
        try:
          self._download_helper.DownloadFile(package_download.url)
        finally:
          os.chdir('..')

      package_filenames[package_name] = package_filename
      package_versions[package_name] = package_download.version

    return package_filenames, package_versions

  def _GetProjectDefinitions(self, projects_file):
    """Retrieves the project definitions from the projects file.

    Args:
      projects_file (str): path to the projects.ini configuration file.

    Returns:
      dist[str, ProjectDefinition]: project definitions per name.
    """
    project_definitions = {}

    with open(projects_file, 'r', encoding='utf-8') as file_object:
      project_definition_reader = projects.ProjectDefinitionReader()
      for project_definition in project_definition_reader.Read(file_object):
        project_definitions[project_definition.name] = project_definition

    return project_definitions

  def _GetUserDefinedWheelPackageNames(
      self, project_definitions, user_defined_project_names):
    """Determines names of wheel packages that should be updated.

    Args:
      project_definitions (dist[str, ProjectDefinition]): project definitions
          per name.
      user_defined_project_names (list[str]): user specified names of projects,
          that should be updated if an update is available. An empty list
          represents all available projects.

    Returns:
      list[str]: names of packages that should be updated if an update is
          available. These package names are derived from the user specified
          names of projects. An empty list represents all available packages.
    """
    user_defined_wheel_package_names = []
    for project_name in user_defined_project_names:
      project_definition = project_definitions.get(project_name, None)
      if not project_definition:
        alternate_name = self._MODULE_ALIASES.get(project_name, None)
        if alternate_name:
          project_definition = project_definitions.get(alternate_name, None)

      if not project_definition:
        logging.error('Missing project definition for package: {0:s}'.format(
            project_name))
        continue

      package_name = getattr(
          project_definition, 'wheel_name', None) or project_name

      package_name = package_name.lower()
      user_defined_wheel_package_names.append(package_name)

    return user_defined_wheel_package_names

  def _InstallWheelPackagesWindows(self, package_filenames, package_versions):
    """Installs wheel packages on Windows.

    Args:
      package_filenames (dict[str, str]): filenames per package.
      package_versions (dict[str, str]): versions per package.

    Returns:
      bool: True if the installation was successful.
    """
    package_paths = [
        os.path.join(self._download_directory, package_filenames[name])
        for name in package_versions]

    result = True
    if package_paths:
      logging.info('Installing: {0:s}'.format(' '.join(package_paths)))

      command = '{0:s} -m pip install {1:s}'.format(
          sys.executable, ' '.join(package_paths))
      exit_code = subprocess.call(command, shell=False)
      if exit_code != 0:
        logging.error('Running: "{0:s}" failed.'.format(command))
        result = False

    return result

  def ExpandPresets(self, preset_definitions, preset_names):
    """Expands preset names to project names.

    Args:
      preset_definitions (dict[str, PresetDefinition]): preset definitions.
      preset_names (str): names of the presets to expand.

    Returns:
      set[str]: project names.
    """
    project_names = set()
    for preset_name in preset_names:
      preset_definition = preset_definitions.get(preset_name, None)
      if not preset_definition:
        continue

      if preset_definition.preset_names:
        sub_project_names = self.ExpandPresets(
            preset_definitions, preset_definition.preset_names)
        project_names = project_names.union(sub_project_names)

      project_names = project_names.union(
          set(preset_definition.project_names))

    return project_names

  def UpdatePackages(self, projects_file, user_defined_project_names):
    """Updates packages.

    Args:
      projects_file (str): path to the projects.ini configuration file.
      user_defined_project_names (list[str]): user specified names of projects,
          that should be updated if an update is available. An empty list
          represents all available projects.

    Returns:
      bool: True if the update was successful.
    """
    project_definitions = self._GetProjectDefinitions(projects_file)

    user_defined_wheel_package_names = self._GetUserDefinedWheelPackageNames(
        project_definitions, user_defined_project_names)

    available_packages = self._GetAvailableWheelPackages()
    if not available_packages:
      logging.error('No packages found.')
      return False

    if not os.path.exists(self._download_directory):
      os.mkdir(self._download_directory)

    package_filenames, package_versions = (
        self._GetWheelPackageFilenamesAndVersions(
            project_definitions, available_packages,
            user_defined_wheel_package_names))

    if self._download_only:
      return True

    return self._InstallWheelPackagesWindows(
        package_filenames, package_versions)


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  tracks = ['dev', 'stable', 'staging', 'testing']

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
      '--preset', dest='preset', action='store',
      metavar='PRESET_NAME', default=None, help=(
          'name of the preset of project names to update. The default is to '
          'update all project defined in the projects.ini configuration file. '
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

  dependency_updater = DependencyUpdater(
      download_directory=options.download_directory,
      download_only=options.download_only,
      download_track=options.track,
      exclude_packages=options.exclude_packages,
      force_install=options.force_install,
      preferred_machine_type=options.machine_type,
      verbose_output=options.verbose)

  user_defined_project_names = []
  if options.preset:
    preset_definitions = {}

    with open(presets_file, 'r', encoding='utf-8') as file_object:
      definition_reader = presets.PresetDefinitionReader()
      preset_definitions = {
          preset_definition.name: preset_definition
          for preset_definition in definition_reader.Read(file_object)}

    user_defined_project_names = dependency_updater.ExpandPresets(
        preset_definitions, options.preset)
    if not user_defined_project_names:
      print('Undefined preset: {0:s}'.format(options.preset))
      print('')
      return False

  elif options.project_names:
    user_defined_project_names = options.project_names

  result = dependency_updater.UpdatePackages(
      projects_file, user_defined_project_names)

  return result


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
