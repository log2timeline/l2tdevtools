# -*- coding: utf-8 -*-
"""Writer for requirements.txt files."""

from __future__ import unicode_literals

from l2tdevtools.dependency_writers import interface


class RequirementsWriter(interface.DependencyFileWriter):
  """Requirements file writer."""

  PATH = 'requirements.txt'

  _FILE_HEADER = ['pip >= 7.0.0']

  def Write(self):
    """Writes a requirements file."""
    python_dependencies = self._GetPyPIPythonDependencies()

    file_content = []
    file_content.extend(self._FILE_HEADER)

    file_content.extend([
        '{0:s}'.format(dependency) for dependency in python_dependencies])

    file_content.append('')

    file_content = '\n'.join(file_content)
    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)


class TestRequirementsWriter(interface.DependencyFileWriter):
  """Test requirements file writer."""

  PATH = 'test_requirements.txt'

  def Write(self):
    """Writes a test requirements file."""
    python_dependencies = self._GetPyPIPythonDependencies()
    test_dependencies = self._GetPyPITestDependencies(python_dependencies)

    file_content = [
        '{0:s}'.format(dependency) for dependency in test_dependencies]

    file_content.append('')

    file_content = '\n'.join(file_content)
    file_content = file_content.encode('utf-8')

    with open(self.PATH, 'wb') as file_object:
      file_object.write(file_content)
