# -*- coding: utf-8 -*-
"""Project definitions."""

import configparser
import logging
import re


class ProjectDefinition(object):
  """Project definition.

  Attributes:
    architecture_dependent (bool): True if the project is architecture
        dependent.
    build_dependencies (list[str]): build dependencies.
    build_system (str): build system.
    configure_options (list[str]): configure options.
    description_long (str): long description of the project.
    description_short (str): short description of the project.
    disabled (list[str]): names of the build targets that are disabled for
        this project.
    download_url (str): source package download URL.
    dpkg_build_dependencies (list[str]): dpkg build dependencies.
    dpkg_configure_options (list[str]): configure options when building a deb.
    dpkg_dependencies (list[str]): dpkg dependencies.
    dpkg_name (str): dpkg package name.
    dpkg_source_name (str): dpkg source package name.
    dpkg_template_additional (list[str]): names of additional dpkg template
        files.
    dpkg_template_control (str): name of the dpkg control template file.
    dpkg_template_install (list[str]): names of the dpkg install template files.
    dpkg_template_install_python3 (list[str]): names of the dpkg Python 3
        install template files.
    dpkg_template_py3dist_overrides (str): name of the dpkg py3dist-overrides
        template file.
    dpkg_template_rules (str): name of the dpkg rules template file.
    dpkg_template_source_options (str): name of the dpkg source options template
        file.
    git_url (str): git repository URL.
    github_release_is_archive (bool): github release is the source archive.
    github_release_prefix (str): github release prefix.
    github_release_tag_prefix (str): github release tag prefix.
    homepage_url (str): project homepage URL.
    license (str): license.
    maintainer (str): name and email address of the maintainer.
    name (str): name of the project.
    optional_build_dependencies (list[str]): optional build dependencies.
    pkg_configure_options (list[str]): configure options when building a pkg.
    pypi_name (str): name of the project on PyPI.
    pypi_source_name (str): name used in the source package file on PyPI.
    rpm_build_dependencies (list[str]): rpm build dependencies.
    rpm_dependencies (list[str]): rpm dependencies.
    rpm_name (str): RPM package name.
    rpm_template_spec (str): name of the rpm spec file.
    setup_name (str): project name used in setup.py.
    srpm_name (str): source RPM package name.
    version (ProjectVersionDefinition): version requirements.
    wheel_name (str): Python wheel package name.
  """

  def __init__(self, name):
    """Initializes a project definition.

    Args:
      name (str): name of the project.
    """
    super(ProjectDefinition, self).__init__()
    self.architecture_dependent = False
    self.build_dependencies = None
    self.build_system = None
    self.configure_options = None
    self.description_long = None
    self.description_short = None
    self.disabled = None
    self.download_url = None
    self.dpkg_build_dependencies = None
    self.dpkg_configure_options = None
    self.dpkg_dependencies = None
    self.dpkg_name = None
    self.dpkg_source_name = None
    self.dpkg_template_additional = None
    self.dpkg_template_control = None
    self.dpkg_template_install = None
    self.dpkg_template_install_python3 = None
    self.dpkg_template_py3dist_overrides = None
    self.dpkg_template_rules = None
    self.dpkg_template_source_options = None
    self.git_url = None
    self.github_release_is_archive = False
    self.github_release_prefix = None
    self.github_release_tag_prefix = None
    self.homepage_url = None
    self.license = None
    self.maintainer = None
    self.name = name
    self.optional_build_dependencies = None
    self.pkg_configure_options = None
    self.pypi_name = None
    self.pypi_source_name = None
    self.rpm_build_dependencies = None
    self.rpm_dependencies = None
    self.rpm_name = None
    self.rpm_template_spec = None
    self.setup_name = None
    self.srpm_name = None
    self.version = None
    self.wheel_name = None


class ProjectVersionDefinition(object):
  """Project version definition."""

  _VERSION_STRING_PART_RE = re.compile(
      r'^(<[=]?|>[=]?|==)([0-9]+)[.]?([0-9]+|)[.]?([0-9]+|)[.-]?([0-9]+|)$')

  def __init__(self, version_string):
    """Initializes a project version definition.

    Args:
      version_string (str): version string.
    """
    super(ProjectVersionDefinition, self).__init__()
    self._version_string_parts = []

    if not version_string:
      return

    version_string_parts = version_string.split(',')
    number_of_version_string_parts = len(version_string_parts)
    if number_of_version_string_parts > 2:
      logging.warning('Unsupported version string: {0:s}'.format(
          version_string))
      return

    self._version_string_parts = []
    for index, version_string_part in enumerate(version_string_parts):
      if index == 1 and not version_string_part.startswith('<'):
        logging.warning('Unsupported version string part: {0:s}'.format(
            version_string_part))
        return

      matches = self._VERSION_STRING_PART_RE.findall(version_string_part)
      if not matches:
        logging.warning('Unsupported version string part: {0:s}'.format(
            version_string_part))
        return

      self._version_string_parts.append([
          match for match in matches[0] if match or match == 0])

    self._version_string = version_string

  @property
  def version_string(self):
    """str: string representation of the object."""
    return self._version_string

  def GetEarliestVersion(self):
    """Retrieves the earliest version.

    Returns:
      str: earliest version or None if version string parts are missing.
    """
    if not self._version_string_parts:
      return None

    return self._version_string_parts[0]

  def GetLatestVersion(self):
    """Retrieves the latest version.

    Returns:
      str: latest version or None if version string parts are missing.
    """
    if not self._version_string_parts or len(self._version_string_parts) == 1:
      return None

    return self._version_string_parts[1]


class ProjectDefinitionReader(object):
  """Project definition reader."""

  def _GetConfigValue(self, config_parser, section_name, value_name):
    """Retrieves a value from the config parser.

    Args:
      config_parser (ConfigParser): configuration parser.
      section_name (str): name of the section that contains the value.
      value_name (str): name of the value.

    Returns:
      object: value or None if the value does not exists.
    """
    try:
      return config_parser.get(section_name, value_name)
    except configparser.NoOptionError:
      return None

  def Read(self, file_object):
    """Reads project definitions.

    Args:
      file_object (file): file-like object to read from.

    Yields:
      ProjectDefinition: project definition.
    """
    config_parser = configparser.ConfigParser(interpolation=None)
    config_parser.read_file(file_object)

    for section_name in config_parser.sections():
      project_definition = ProjectDefinition(section_name)

      project_definition.architecture_dependent = self._GetConfigValue(
          config_parser, section_name, 'architecture_dependent')
      project_definition.build_dependencies = self._GetConfigValue(
          config_parser, section_name, 'build_dependencies')
      project_definition.optional_build_dependencies = self._GetConfigValue(
          config_parser, section_name, 'optional_build_dependencies')
      project_definition.build_system = self._GetConfigValue(
          config_parser, section_name, 'build_system')
      project_definition.configure_options = self._GetConfigValue(
          config_parser, section_name, 'configure_options')
      project_definition.description_long = self._GetConfigValue(
          config_parser, section_name, 'description_long')
      project_definition.description_short = self._GetConfigValue(
          config_parser, section_name, 'description_short')
      project_definition.disabled = self._GetConfigValue(
          config_parser, section_name, 'disabled')
      project_definition.dpkg_build_dependencies = self._GetConfigValue(
          config_parser, section_name, 'dpkg_build_dependencies')
      project_definition.dpkg_configure_options = self._GetConfigValue(
          config_parser, section_name, 'dpkg_configure_options')
      project_definition.dpkg_dependencies = self._GetConfigValue(
          config_parser, section_name, 'dpkg_dependencies')
      project_definition.dpkg_name = self._GetConfigValue(
          config_parser, section_name, 'dpkg_name')
      project_definition.dpkg_source_name = self._GetConfigValue(
          config_parser, section_name, 'dpkg_source_name')
      project_definition.dpkg_template_additional = self._GetConfigValue(
          config_parser, section_name, 'dpkg_template_additional')
      project_definition.dpkg_template_control = self._GetConfigValue(
          config_parser, section_name, 'dpkg_template_control')
      project_definition.dpkg_template_install = self._GetConfigValue(
          config_parser, section_name, 'dpkg_template_install')
      project_definition.dpkg_template_install_python3 = self._GetConfigValue(
          config_parser, section_name, 'dpkg_template_install_python3')
      project_definition.dpkg_template_py3dist_overrides = self._GetConfigValue(
          config_parser, section_name, 'dpkg_template_py3dist_overrides')
      project_definition.dpkg_template_rules = self._GetConfigValue(
          config_parser, section_name, 'dpkg_template_rules')
      project_definition.dpkg_template_source_options = self._GetConfigValue(
          config_parser, section_name, 'dpkg_template_source_options')
      project_definition.download_url = self._GetConfigValue(
          config_parser, section_name, 'download_url')
      project_definition.git_url = self._GetConfigValue(
          config_parser, section_name, 'git_url')
      project_definition.github_release_is_archive = self._GetConfigValue(
          config_parser, section_name, 'github_release_is_archive')
      project_definition.github_release_prefix = self._GetConfigValue(
          config_parser, section_name, 'github_release_prefix')
      project_definition.github_release_tag_prefix = self._GetConfigValue(
          config_parser, section_name, 'github_release_tag_prefix')
      project_definition.homepage_url = self._GetConfigValue(
          config_parser, section_name, 'homepage_url')
      project_definition.license = self._GetConfigValue(
          config_parser, section_name, 'license')
      project_definition.maintainer = self._GetConfigValue(
          config_parser, section_name, 'maintainer')
      project_definition.rpm_build_dependencies = self._GetConfigValue(
          config_parser, section_name, 'rpm_build_dependencies')
      project_definition.rpm_dependencies = self._GetConfigValue(
          config_parser, section_name, 'rpm_dependencies')
      project_definition.rpm_name = self._GetConfigValue(
          config_parser, section_name, 'rpm_name')
      project_definition.rpm_template_spec = self._GetConfigValue(
          config_parser, section_name, 'rpm_template_spec')
      project_definition.pkg_configure_options = self._GetConfigValue(
          config_parser, section_name, 'pkg_configure_options')
      project_definition.pypi_name = self._GetConfigValue(
          config_parser, section_name, 'pypi_name')
      project_definition.pypi_source_name = self._GetConfigValue(
          config_parser, section_name, 'pypi_source_name')
      project_definition.setup_name = self._GetConfigValue(
          config_parser, section_name, 'setup_name')
      project_definition.srpm_name = self._GetConfigValue(
          config_parser, section_name, 'srpm_name')
      project_definition.version = self._GetConfigValue(
          config_parser, section_name, 'version')
      project_definition.wheel_name = self._GetConfigValue(
          config_parser, section_name, 'wheel_name')

      if project_definition.build_dependencies is None:
        project_definition.build_dependencies = []
      elif isinstance(project_definition.build_dependencies, str):
        project_definition.build_dependencies = (
            project_definition.build_dependencies.split(','))

      if project_definition.configure_options is None:
        project_definition.configure_options = []
      elif isinstance(project_definition.configure_options, str):
        project_definition.configure_options = (
            project_definition.configure_options.split(','))

      if project_definition.disabled is None:
        project_definition.disabled = []
      elif isinstance(project_definition.disabled, str):
        project_definition.disabled = project_definition.disabled.split(
            ',')

      if project_definition.dpkg_build_dependencies is None:
        project_definition.dpkg_build_dependencies = []
      elif isinstance(project_definition.dpkg_build_dependencies, str):
        project_definition.dpkg_build_dependencies = (
            project_definition.dpkg_build_dependencies.split(','))

      if project_definition.dpkg_configure_options is None:
        project_definition.dpkg_configure_options = []
      elif isinstance(project_definition.dpkg_configure_options, str):
        project_definition.dpkg_configure_options = (
            project_definition.dpkg_configure_options.split(','))

      if project_definition.dpkg_dependencies is None:
        project_definition.dpkg_dependencies = []
      elif isinstance(project_definition.dpkg_dependencies, str):
        project_definition.dpkg_dependencies = (
            project_definition.dpkg_dependencies.split(','))

      if project_definition.dpkg_template_additional is None:
        project_definition.dpkg_template_additional = []
      elif isinstance(project_definition.dpkg_template_additional, str):
        project_definition.dpkg_template_additional = (
            project_definition.dpkg_template_additional.split(','))

      if project_definition.dpkg_template_install is None:
        project_definition.dpkg_template_install = []
      elif isinstance(project_definition.dpkg_template_install, str):
        project_definition.dpkg_template_install = (
            project_definition.dpkg_template_install.split(','))

      if project_definition.dpkg_template_install_python3 is None:
        project_definition.dpkg_template_install_python3 = []
      elif isinstance(project_definition.dpkg_template_install_python3, str):
        project_definition.dpkg_template_install_python3 = (
            project_definition.dpkg_template_install_python3.split(','))

      if project_definition.rpm_build_dependencies is None:
        project_definition.rpm_build_dependencies = []
      elif isinstance(project_definition.rpm_build_dependencies, str):
        project_definition.rpm_build_dependencies = (
            project_definition.rpm_build_dependencies.split(','))

      if project_definition.rpm_dependencies is None:
        project_definition.rpm_dependencies = []
      elif isinstance(project_definition.rpm_dependencies, str):
        project_definition.rpm_dependencies = (
            project_definition.rpm_dependencies.split(','))

      if project_definition.pkg_configure_options is None:
        project_definition.pkg_configure_options = []
      elif isinstance(project_definition.pkg_configure_options, str):
        project_definition.pkg_configure_options = (
            project_definition.pkg_configure_options.split(','))

      # Need at minimum a name and a download URL.
      if project_definition.name and project_definition.download_url:
        yield project_definition

      project_definition.version = ProjectVersionDefinition(
          project_definition.version)
