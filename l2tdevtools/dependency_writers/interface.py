# -*- coding: utf-8 -*-
"""Helper for writing files that contain dependency information."""

from __future__ import unicode_literals

import abc
import io
import string


class DependencyFileWriter(object):
  """Base class for dependency file writers."""

  def __init__(
      self, l2tdevtools_path, project_definition, dependency_helper,
      test_dependency_helper):
    """Initializes a dependency file writer.

    Args:
      l2tdevtools_path (str): path to l2tdevtools.
      project_definition (ProjectDefinition): project definition.
      dependency_helper (DependencyHelper): dependency helper.
      test_dependency_helper (DependencyHelper): test dependency helper
          or None if not available.
    """
    super(DependencyFileWriter, self).__init__()
    self._dependency_helper = dependency_helper
    self._l2tdevtools_path = l2tdevtools_path
    self._project_definition = project_definition
    self._test_dependency_helper = test_dependency_helper

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

  def _GetDPKGPythonDependencies(self, python_version=2):
    """Retrieves DPKG Python dependencies.

    Args:
      python_version (Optional[int]): Python major version.

    Returns:
      list[str]: DPKG package names of Python dependencies.
    """
    return self._dependency_helper.GetDPKGDepends(
        exclude_version=True, python_version=python_version)

  def _GetDPKGTestDependencies(self, python_dependencies, python_version=2):
    """Retrieves DPKG test dependencies.

    Args:
      python_dependencies (list[str]): DPKG package names of Python
          dependencies.
      python_version (Optional[int]): Python major version.

    Returns:
      list[str]: DPKG package names of test dependencies.
    """
    test_dependencies = self._test_dependency_helper.GetDPKGDepends(
        exclude_version=True, python_version=python_version)

    # TODO: replace by test_dependencies.ini or dev_dependencies.ini or equiv.
    if python_version == 2:
      test_dependencies.extend(['python-setuptools'])
    else:
      test_dependencies.extend(['python3-distutils', 'python3-setuptools'])

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
    test_dependencies = self._test_dependency_helper.GetInstallRequires(
        exclude_version=exclude_version)

    return [
        test_dependency for test_dependency in test_dependencies
        if test_dependency not in python_dependencies]

  def _GetRPMPythonDependencies(self, python_version=2):
    """Retrieves RPM Python dependencies.

    Args:
      python_version (Optional[int]): Python major version.

    Returns:
      list[str]: RPM package names of Python dependencies.
    """
    return self._dependency_helper.GetRPMRequires(
        exclude_version=True, python_version=python_version)

  def _GetRPMTestDependencies(self, python_dependencies, python_version=2):
    """Retrieves RPM test dependencies.

    Args:
      python_dependencies (list[str]): RPM package names of Python dependencies.
      python_version (Optional[int]): Python major version.

    Returns:
      list[str]: RPM package names of test dependencies.
    """
    test_dependencies = self._test_dependency_helper.GetRPMRequires(
        exclude_version=True, python_version=python_version)

    # TODO: replace by test_dependencies.ini or dev_dependencies.ini or equiv.
    if python_version == 2:
      test_dependencies.extend(['python2-setuptools'])
    else:
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
    with io.open(filename, 'r', encoding='utf-8') as file_object:
      file_data = file_object.read()

    return string.Template(file_data)

  @abc.abstractmethod
  def Write(self):
    """Writes the file or files produced by the file writer."""
