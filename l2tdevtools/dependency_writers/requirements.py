# -*- coding: utf-8 -*-
"""Writer for requirements.txt files."""

from l2tdevtools.dependency_writers import interface


class RequirementsWriter(interface.DependencyFileWriter):
  """Requirements file writer."""

  PATH = 'requirements.txt'

  def Write(self):
    """Writes a requirements file."""
    python_dependencies = self._GetPyPIPythonDependencies()

    file_content = [str(dependency) for dependency in python_dependencies]

    file_content.append('')

    file_content = '\n'.join(file_content)

    with open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)


class TestRequirementsWriter(interface.DependencyFileWriter):
  """Test requirements file writer."""

  PATH = 'test_requirements.txt'

  def Write(self):
    """Writes a test requirements file."""
    python_dependencies = self._GetPyPIPythonDependencies()
    test_dependencies = self._GetPyPITestDependencies(python_dependencies)

    file_content = [str(dependency) for dependency in test_dependencies]

    file_content.append('')

    file_content = '\n'.join(file_content)

    with open(self.PATH, 'w', encoding='utf-8') as file_object:
      file_object.write(file_content)
