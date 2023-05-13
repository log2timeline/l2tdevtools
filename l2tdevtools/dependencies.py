# -*- coding: utf-8 -*-
"""Helper to check for availability and version of dependencies."""

import configparser
import os
import re


class DependencyDefinition(object):
  """Dependency definition.

  Attributes:
    dpkg_name (str): name of the dpkg package that provides the dependency.
    is_optional (bool): True if the dependency is optional.
    l2tbinaries_name (str): name of the l2tbinaries package that provides
        the dependency.
    maximum_version (str): maximum supported version, a greater or equal
        version is not supported.
    minimum_version (str): minimum supported version, a lesser version is
        not supported.
    name (str): name of (the Python module that provides) the dependency.
    pypi_name (str): name of the PyPI package that provides the dependency.
    python2_only (bool): True if the dependency is only supported by Python 2.
    python3_only (bool): True if the dependency is only supported by Python 3.
    rpm_name (str): name of the rpm package that provides the dependency.
    skip_check (bool): True if the dependency should be skipped by the
        CheckDependencies or CheckTestDependencies methods of DependencyHelper.
    skip_requires (bool): True if the dependency should be excluded from
        requirements.txt or setup.py install_requires.
    version_property (str): name of the version attribute or function.
  """

  def __init__(self, name):
    """Initializes a dependency configuration.

    Args:
      name (str): name of the dependency.
    """
    super(DependencyDefinition, self).__init__()
    self.dpkg_name = None
    self.is_optional = False
    self.l2tbinaries_name = None
    self.maximum_version = None
    self.minimum_version = None
    self.name = name
    self.pypi_name = None
    self.python2_only = False
    self.python3_only = False
    self.rpm_name = None
    self.skip_check = None
    self.skip_requires = None
    self.version_property = None


class DependencyDefinitionReader(object):
  """Dependency definition reader."""

  _VALUE_NAMES = frozenset([
      'dpkg_name',
      'is_optional',
      'l2tbinaries_name',
      'maximum_version',
      'minimum_version',
      'pypi_name',
      'python2_only',
      'python3_only',
      'rpm_name',
      'skip_check',
      'skip_requires',
      'version_property'])

  def _GetConfigValue(self, config_parser, section_name, value_name):
    """Retrieves a value from the config parser.

    Args:
      config_parser (ConfigParser): configuration parser.
      section_name (str): name of the section that contains the value.
      value_name (str): name of the value.

    Returns:
      object: configuration value or None if the value does not exists.
    """
    try:
      return config_parser.get(section_name, value_name)
    except configparser.NoOptionError:
      return None

  def Read(self, file_object):
    """Reads dependency definitions.

    Args:
      file_object (file): file-like object to read from.

    Yields:
      DependencyDefinition: dependency definition.
    """
    config_parser = configparser.ConfigParser(interpolation=None)
    config_parser.read_file(file_object)

    for section_name in config_parser.sections():
      dependency_definition = DependencyDefinition(section_name)
      for value_name in self._VALUE_NAMES:
        value = self._GetConfigValue(config_parser, section_name, value_name)
        setattr(dependency_definition, value_name, value)

      yield dependency_definition


class DependencyHelper(object):
  """Dependency helper.

  Attributes:
    dependencies (dict[str, DependencyDefinition]): dependencies.
  """

  _VERSION_NUMBERS_REGEX = re.compile(r'[0-9.]+')
  _VERSION_SPLIT_REGEX = re.compile(r'\.|\-')

  def __init__(
      self, dependencies_file='dependencies.ini',
      test_dependencies_file='test_dependencies.ini'):
    """Initializes a dependency helper.

    Args:
      dependencies_file (Optional[str]): path to the dependencies configuration
          file.
      test_dependencies_file (Optional[str]): path to the test dependencies
          configuration file.
    """
    super(DependencyHelper, self).__init__()
    self._test_dependencies = {}
    self.dependencies = {}

    dependency_reader = DependencyDefinitionReader()

    with open(dependencies_file, 'r', encoding='utf-8') as file_object:
      for dependency in dependency_reader.Read(file_object):
        self.dependencies[dependency.name] = dependency

    if os.path.exists(test_dependencies_file):
      with open(test_dependencies_file, 'r', encoding='utf-8') as file_object:
        for dependency in dependency_reader.Read(file_object):
          self._test_dependencies[dependency.name] = dependency

  def _CheckPythonModule(self, dependency):
    """Checks the availability of a Python module.

    Args:
      dependency (DependencyDefinition): dependency definition.

    Returns:
      tuple: containing:

        bool: True if the Python module is available and conforms to
            the minimum required version, False otherwise.
        str: status message.
    """
    module_object = self._ImportPythonModule(dependency.name)
    if not module_object:
      return False, f'missing: {dependency.name:s}'

    if not dependency.version_property:
      return True, dependency.name

    return self._CheckPythonModuleVersion(
        dependency.name, module_object, dependency.version_property,
        dependency.minimum_version, dependency.maximum_version)

  def _CheckPythonModuleVersion(
      self, module_name, module_object, version_property, minimum_version,
      maximum_version):
    """Checks the version of a Python module.

    Args:
      module_object (module): Python module.
      module_name (str): name of the Python module.
      version_property (str): version attribute or function.
      minimum_version (str): minimum version.
      maximum_version (str): maximum version.

    Returns:
      tuple: containing:

        bool: True if the Python module is available and conforms to
            the minimum required version, False otherwise.
        str: status message.
    """
    module_version = None
    if not version_property.endswith('()'):
      module_version = getattr(module_object, version_property, None)
    else:
      version_method = getattr(
          module_object, version_property[:-2], None)
      if version_method:
        module_version = version_method()

    if not module_version:
      return False, (
          f'unable to determine version information for: {module_name:s}')

    # Make sure the module version is a string.
    module_version = f'{module_version!s}'

    # Split the version string and convert every digit into an integer.
    # A string compare of both version strings will yield an incorrect result.

    # Strip any semantic suffixes such as a1, b1, pre, post, rc, dev.
    module_version = self._VERSION_NUMBERS_REGEX.findall(module_version)[0]

    if module_version[-1] == '.':
      module_version = module_version[:-1]

    try:
      module_version_map = list(
          map(int, self._VERSION_SPLIT_REGEX.split(module_version)))
    except ValueError:
      return False, (
          f'unable to parse module version: {module_name:s} {module_version:s}')

    if minimum_version:
      try:
        minimum_version_map = list(
            map(int, self._VERSION_SPLIT_REGEX.split(minimum_version)))
      except ValueError:
        return False, (
            f'unable to parse minimum version: {module_name:s} '
            f'{minimum_version:s}')

      if module_version_map < minimum_version_map:
        return False, (
            f'{module_name:s} version: {module_version!s} is too old, '
            f'{minimum_version!s} or later required')

    if maximum_version:
      try:
        maximum_version_map = list(
            map(int, self._VERSION_SPLIT_REGEX.split(maximum_version)))
      except ValueError:
        return False, (
            f'unable to parse maximum version: {module_name:s} '
            f'{maximum_version:s}')

      if module_version_map > maximum_version_map:
        return False, (
            f'{module_name:s} version: {module_version!s} is too recent, '
            f'{maximum_version!s} or earlier required')

    return True, f'{module_name:s} version: {module_version!s}'

  def _ImportPythonModule(self, module_name):
    """Imports a Python module.

    Args:
      module_name (str): name of the module.

    Returns:
      module: Python module or None if the module cannot be imported.
    """
    try:
      module_object = list(map(__import__, [module_name]))[0]
    except ImportError:
      return None

    # If the module name contains dots get the upper most module object.
    if '.' in module_name:
      for submodule_name in module_name.split('.')[1:]:
        module_object = getattr(module_object, submodule_name, None)

    return module_object

  def _PrintCheckDependencyStatus(
      self, dependency, result, status_message, verbose_output=True):
    """Prints the check dependency status.

    Args:
      dependency (DependencyDefinition): dependency definition.
      result (bool): True if the Python module is available and conforms to
            the minimum required version, False otherwise.
      status_message (str): status message.
      verbose_output (Optional[bool]): True if output should be verbose.
    """
    if not result or dependency.is_optional:
      if dependency.is_optional:
        status_indicator = '[OPTIONAL]'
      else:
        status_indicator = '[FAILURE]'

      print(f'{status_indicator:s}\t{status_message:s}')

    elif verbose_output:
      print(f'[OK]\t\t{status_message:s}')

  def CheckDependencies(self, verbose_output=True):
    """Checks the availability of the dependencies.

    Args:
      verbose_output (Optional[bool]): True if output should be verbose.

    Returns:
      bool: True if the dependencies are available, False otherwise.
    """
    print('Checking availability and versions of dependencies.')
    check_result = True

    for _, dependency in sorted(self.dependencies.items()):
      if dependency.skip_check:
        continue

      result, status_message = self._CheckPythonModule(dependency)

      if not result and not dependency.is_optional:
        check_result = False

      self._PrintCheckDependencyStatus(
          dependency, result, status_message, verbose_output=verbose_output)

    if check_result and not verbose_output:
      print('[OK]')

    print('')
    return check_result

  def CheckTestDependencies(self, verbose_output=True):
    """Checks the availability of the dependencies when running tests.

    Args:
      verbose_output (Optional[bool]): True if output should be verbose.

    Returns:
      bool: True if the dependencies are available, False otherwise.
    """
    if not self.CheckDependencies(verbose_output=verbose_output):
      return False

    print('Checking availability and versions of test dependencies.')
    check_result = True

    for dependency in sorted(
        self._test_dependencies.values(),
        key=lambda dependency: dependency.name):
      if dependency.skip_check:
        continue

      result, status_message = self._CheckPythonModule(dependency)

      if not result and not dependency.is_optional:
        check_result = False

      self._PrintCheckDependencyStatus(
          dependency, result, status_message, verbose_output=verbose_output)

    if check_result and not verbose_output:
      print('[OK]')

    print('')
    return check_result

  # The following functions should not be included in utils/dependencies.py

  def _GetDPKGDepends(self, dependencies, exclude_version=False):
    """Retrieves the DPKG control file installation requirements.

    Args:
      dependencies (dict[str, DependencyDefinition]): dependencies.
      exclude_version (Optional[bool]): True if the version should be excluded
          from the dependency definitions.

    Returns:
      list[str]: dependency definitions for requires for DPKG control file.
    """
    requires = []
    for dependency in sorted(
        dependencies.values(), key=lambda dependency: dependency.name):
      module_name = dependency.dpkg_name or dependency.name
      if 'python2' in module_name:
        module_name = module_name.replace('python2', 'python3')
      elif 'python3' not in module_name:
        module_name = module_name.replace('python', 'python3')

      if exclude_version or not dependency.minimum_version:
        requires_string = module_name
      else:
        requires_string = f'{module_name:s} (>= {dependency.minimum_version:s})'

      requires.append(requires_string)

    return sorted(requires)

  def _GetInstallRequires(self, dependencies, exclude_version=False):
    """Retrieves the setup.py installation requirements.

    Args:
      dependencies (dict[str, DependencyDefinition]): dependencies.
      exclude_version (Optional[bool]): True if the version should be excluded
          from the dependency definitions.

    Returns:
      list[str]: dependency definitions for install_requires in setup.py.
    """
    install_requires = []
    for dependency in sorted(
        dependencies.values(), key=lambda dependency: dependency.name):
      if dependency.skip_requires:
        continue

      module_name = dependency.pypi_name or dependency.name

      # Use the sqlite3 module provided by the standard library.
      if module_name == 'pysqlite':
        continue

      requires_part = []
      if not exclude_version:
        if dependency.minimum_version:
          requires_part.append(f'>= {dependency.minimum_version!s}')
        if dependency.maximum_version:
          requires_part.append(f'< {dependency.maximum_version!s}')

      requires_string = module_name
      if requires_part:
        requires_string = ' '.join([requires_string, ','.join(requires_part)])

      if module_name == 'pyxattr':
        requires_string = f'{requires_string:s} ; platform_system != "Windows"'

      install_requires.append(requires_string)

    return sorted(install_requires)

  def _GetL2TBinaries(self, dependencies):
    """Retrieves the l2tbinaries requirements.

    Args:
      dependencies (dict[str, DependencyDefinition]): dependencies.

    Returns:
      list[str]: dependency definitions for l2tbinaries.
    """
    requires = []
    for dependency in sorted(
        dependencies.values(), key=lambda dependency: dependency.name):
      if dependency.l2tbinaries_name:
        module_name = dependency.l2tbinaries_name
      else:
        module_name = dependency.name

      requires.append(module_name)

    return sorted(requires)

  def _GetRPMRequires(self, dependencies, exclude_version=False):
    """Retrieves the setup.cfg RPM installation requirements.

    Args:
      dependencies (dict[str, DependencyDefinition]): dependencies.
      exclude_version (Optional[bool]): True if the version should be excluded
          from the dependency definitions.

    Returns:
      list[str]: dependency definitions for requires for setup.cfg.
    """
    requires = []
    for dependency in sorted(
        dependencies.values(), key=lambda dependency: dependency.name):
      module_name = dependency.rpm_name or dependency.name
      if module_name.startswith('python-'):
        module_name = module_name.replace('python-', 'python3-')
      else:
        module_name = module_name.replace('python2-', 'python3-')
      if module_name.endswith('-python'):
        module_name = module_name.replace('-python', '-python3')
      else:
        module_name = module_name.replace('-python2', '-python3')

      if exclude_version or not dependency.minimum_version:
        requires_string = module_name
      else:
        requires_string = f'{module_name:s} >= {dependency.minimum_version:s}'

      requires.append(requires_string)

    return sorted(requires)

  def GetDPKGDepends(self, exclude_version=False, test_dependencies=False):
    """Retrieves the DPKG control file installation requirements.

    Args:
      exclude_version (Optional[bool]): True if the version should be excluded
          from the dependency definitions.
      test_dependencies (Optional[bool]): True if the test dependencies should
          returned instead of the regual dependencies.

    Returns:
      list[str]: dependency definitions for requires for DPKG control file.
    """
    if test_dependencies:
      dependencies = self._test_dependencies
    else:
      dependencies = self.dependencies

    return self._GetDPKGDepends(dependencies, exclude_version=exclude_version)

  def GetL2TBinaries(self, test_dependencies=False):
    """Retrieves the l2tbinaries requirements.

    Args:
      test_dependencies (Optional[bool]): True if the test dependencies should
          returned instead of the regual dependencies.

    Returns:
      list[str]: dependency definitions for l2tbinaries.
    """
    if test_dependencies:
      dependencies = self._test_dependencies
    else:
      dependencies = self.dependencies

    return self._GetL2TBinaries(dependencies)

  def GetInstallRequires(self, exclude_version=False, test_dependencies=False):
    """Retrieves the setup.py installation requirements.

    Args:
      exclude_version (Optional[bool]): True if the version should be excluded
          from the dependency definitions.
      test_dependencies (Optional[bool]): True if the test dependencies should
          returned instead of the regual dependencies.

    Returns:
      list[str]: dependency definitions for install_requires in setup.py.
    """
    if test_dependencies:
      dependencies = self._test_dependencies
    else:
      dependencies = self.dependencies

    return self._GetInstallRequires(
        dependencies, exclude_version=exclude_version)

  def GetPylintRcExtensionPkgs(self):
    """Retrieves the .pylintrc extension packages.

    Returns:
      list[str]: name of packages for extension-pkg-whitelist in .pylintrc.
    """
    # Do not move to a class constant due to how DependencyHelper is used
    # to generate utils.DependencyHelper of the individual projects.
    names = (
        'pybde',
        'pycaes',
        'pycreg',
        'pyesedb',
        'pyevt',
        'pyevtx',
        'pyewf',
        'pyexe',
        'pyfmos',
        'pyfsapfs',
        'pyfsext',
        'pyfsfat',
        'pyfshfs',
        'pyfsntfs',
        'pyfsxfs',
        'pyfvde',
        'pyfwevt',
        'pyfwnt',
        'pyfwsi',
        'pylnk',
        'pyluksde',
        'pymodi',
        'pymsiecf',
        'pyolecf',
        'pyphdi',
        'pyqcow',
        'pyregf',
        'pyscca',
        'pysigscan',
        'pysmdev',
        'pysmraw',
        'pytsk3',
        'pyvhdi',
        'pyvmdk',
        'pyvshadow',
        'pyvsapm',
        'pyvsbsdl',
        'pyvsgpt',
        'pyvslvm',
        'pyvsmbr',
        'pywrc',
        'xattr',
        'yara')

    extension_packages = []
    for dependency in sorted(
        self.dependencies.values(), key=lambda dependency: dependency.name):
      if dependency.name not in names:
        continue

      extension_packages.append(dependency.name)

    return sorted(extension_packages)

  def GetRPMRequires(self, exclude_version=False, test_dependencies=False):
    """Retrieves the setup.cfg RPM installation requirements.

    Args:
      exclude_version (Optional[bool]): True if the version should be excluded
          from the dependency definitions.
      test_dependencies (Optional[bool]): True if the test dependencies should
          returned instead of the regual dependencies.

    Returns:
      list[str]: dependency definitions for requires for setup.cfg.
    """
    if test_dependencies:
      dependencies = self._test_dependencies
    else:
      dependencies = self.dependencies

    return self._GetRPMRequires(dependencies, exclude_version=exclude_version)
