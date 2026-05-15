"""Writer for dependencies.py files."""

import os

from l2tdevtools.dependency_writers import interface


class DependenciesPyWriter(interface.DependencyFileWriter):
    """Dependencies.py file writer."""

    _TEMPLATE_FILE = os.path.join("data", "templates", "dependencies.py")

    PATH = os.path.join("plaso", "dependencies.py")

    def Write(self):
        """Writes a dependencies.py file."""
        dependencies = []
        for dependency in sorted(
            self._dependency_helper.dependencies.values(),
            key=lambda dependency: dependency.name.lower(),
        ):
            if not dependency.skip_check:
                dependencies.append(dependency)

        python_dependencies = []
        for dependency in dependencies:
            if dependency.maximum_version:
                maximum_version = f"'{dependency.maximum_version:s}'"
            else:
                maximum_version = "None"

            version_property = dependency.version_property or ""
            minimum_version = dependency.minimum_version or ""
            not_optional = not dependency.is_optional

            python_dependency = (
                f"    '{dependency.name:s}': ('{version_property:s}', "
                f"'{minimum_version:s}', {maximum_version:s}, {not_optional!s})"
            )

            python_dependencies.append(python_dependency)

        python_dependencies = ",\n".join(python_dependencies)

        template_mappings = {"python_dependencies": python_dependencies}

        template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
        file_content = self._GenerateFromTemplate(template_file, template_mappings)

        with open(self.PATH, "w", encoding="utf-8") as file_object:
            file_object.write(file_content)
