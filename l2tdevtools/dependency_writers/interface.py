# -*- coding: utf-8 -*-
"""Helper for writing files that contain dependency information."""

import abc
import string


class DependencyFileWriter(object):
  """Base class for dependency file writers."""

  def __init__(
      self, l2tdevtools_path, project_definition, dependency_helper):
    """Initializes a dependency file writer.

    Args:
      l2tdevtools_path (str): path to l2tdevtools.
      project_definition (ProjectDefinition): project definition.
      dependency_helper (DependencyHelper): dependency helper.
    """
    super(DependencyFileWriter, self).__init__()
    self._dependency_helper = dependency_helper
    self._l2tdevtools_path = l2tdevtools_path
    self._project_definition = project_definition

  def _GenerateFromTemplate(self, template_filename, template_mappings):
    """Generates file context based on a template file.

    Args:
      template_filename (str): path of the template file.
      template_mappings (dict[str, str]): template mappings, where the key
          maps to the name of a template variable.

    Returns:
      str: output based on the template string.

    Raises:
      RuntimeError: if the template cannot be formatted.
    """
    template_string = self._ReadTemplateFile(template_filename)

    try:
      return template_string.substitute(template_mappings)

    except (KeyError, ValueError) as exception:
      raise RuntimeError(
          'Unable to format template: {0:s} with error: {1!s}'.format(
              template_filename, exception))

  def _GetDPKGDevDependencies(self):
    """Retrieves DPKG development dependencies.

    Returns:
      list[str]: DPKG package names of development dependencies.
    """
    dpkg_dependencies = self._dependency_helper.GetDPKGDepends(
        exclude_version=True)

    dpkg_dev_dependencies = []

    # TODO: extract from configuration.

    if 'python3-snappy' in dpkg_dependencies:
      dpkg_dev_dependencies.append('libsnappy-dev')

    if 'python3-yara' in dpkg_dependencies:
      dpkg_dev_dependencies.append('libssl-dev')

    if 'python3-xattr' in dpkg_dependencies:
      dpkg_dev_dependencies.append('libffi-dev')

    return dpkg_dev_dependencies

  def _GetDPKGPythonDependencies(self):
    """Retrieves DPKG Python dependencies.

    Returns:
      list[str]: DPKG package names of Python dependencies.
    """
    dpkg_dependencies = self._dependency_helper.GetDPKGDepends(
        exclude_version=True)

    return dpkg_dependencies

  def _GetDPKGTestDependencies(self, python_dependencies):
    """Retrieves DPKG test dependencies.

    Args:
      python_dependencies (list[str]): DPKG package names of Python
          dependencies.

    Returns:
      list[str]: DPKG package names of test dependencies.
    """
    test_dependencies = self._dependency_helper.GetDPKGDepends(
        exclude_version=True, test_dependencies=True)

    return [
        test_dependency for test_dependency in sorted(test_dependencies)
        if test_dependency not in python_dependencies]

  def _GetPyPIPythonDependencies(self, exclude_version=False):
    """Retrieves PyPI Python dependencies.

    Args:
      exclude_version (Optional[bool]): True if the version should be excluded
          from the dependency definitions.

    Returns:
      list[str]: PyPI package names of Python dependencies.
    """
    return self._dependency_helper.GetInstallRequires(
        exclude_version=exclude_version)

  def _GetPyPITestDependencies(
      self, python_dependencies, exclude_version=False):
    """Retrieves PyPI test dependencies.

    Args:
      python_dependencies (list[str]): PyPI package names of Python
          dependencies.
      exclude_version (Optional[bool]): True if the version should be excluded
          from the dependency definitions.

    Returns:
      list[str]: PyPI package names of test dependencies.
    """
    test_dependencies = self._dependency_helper.GetInstallRequires(
        exclude_version=exclude_version, test_dependencies=True)

    return [
        test_dependency for test_dependency in test_dependencies
        if test_dependency not in python_dependencies]

  def _GetRPMPythonDependencies(self):
    """Retrieves RPM Python dependencies.

    Returns:
      list[str]: RPM package names of Python dependencies.
    """
    return self._dependency_helper.GetRPMRequires(exclude_version=True)

  def _GetRPMTestDependencies(self, python_dependencies):
    """Retrieves RPM test dependencies.

    Args:
      python_dependencies (list[str]): RPM package names of Python dependencies.

    Returns:
      list[str]: RPM package names of test dependencies.
    """
    test_dependencies = self._dependency_helper.GetRPMRequires(
        exclude_version=True, test_dependencies=True)

    # TODO: replace by test_dependencies.ini or dev_dependencies.ini or equiv.
    test_dependencies.extend(['python3-setuptools'])

    return [
        test_dependency for test_dependency in sorted(test_dependencies)
        if test_dependency not in python_dependencies]

  def _ReadTemplateFile(self, filename):
    """Reads a template string from file.

    Args:
      filename (str): name of the file containing the template string.

    Returns:
      string.Template: template string.
    """
    with open(filename, 'r', encoding='utf-8') as file_object:
      file_data = file_object.read()

    return string.Template(file_data)

  @abc.abstractmethod
  def Write(self):
    """Writes the file or files produced by the file writer."""
