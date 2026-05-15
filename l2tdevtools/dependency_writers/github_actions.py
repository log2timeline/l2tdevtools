"""Writer for GitHub actions workflow files."""

import glob
import os

from l2tdevtools.dependency_writers import interface


class GitHubActionsLintYmlWriter(interface.DependencyFileWriter):
    """lint.yml GitHub actions workflow file writer."""

    _TEMPLATE_DIRECTORY = os.path.join(
        "data", "templates", "github_actions", "lint.yml"
    )

    PATH = os.path.join(".github", "workflows", "lint.yml")

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
        template_filename = os.path.join(
            self._l2tdevtools_path, self._TEMPLATE_DIRECTORY, template_filename
        )
        return super()._GenerateFromTemplate(template_filename, template_mappings)

    def Write(self):
        """Writes a lint.yml GitHub actions workflow file ."""
        dpkg_dependencies = self._GetDPKGPythonDependencies()
        test_dependencies = self._GetDPKGTestDependencies(dpkg_dependencies)
        dpkg_dependencies.extend(test_dependencies)
        dpkg_dependencies.extend(["python3-pip", "python3-setuptools", "tox"])

        dpkg_dev_dependencies = self._GetDPKGDevDependencies()

        template_mappings = {
            "dpkg_dependencies": " ".join(sorted(set(dpkg_dependencies))),
            "dpkg_dev_dependencies": " ".join(sorted(set(dpkg_dev_dependencies))),
        }

        python_module_name = self._project_definition.name

        if self._project_definition.name.endswith("-kb"):
            python_module_name = "".join([python_module_name[:-3], "rc"])

        paths_to_lint_yaml = []

        if os.path.isdir(python_module_name):
            if glob.glob(
                os.path.join(python_module_name, "**", "*.yaml"), recursive=True
            ):
                paths_to_lint_yaml.append(python_module_name)

        if os.path.isdir("data"):
            if glob.glob(os.path.join("data", "**", "*.yaml"), recursive=True):
                paths_to_lint_yaml.append("data")

        if os.path.isdir("test_data"):
            if glob.glob(os.path.join("test_data", "**", "*.yaml"), recursive=True):
                paths_to_lint_yaml.append("test_data")

        if os.path.isdir("tests"):
            if glob.glob(os.path.join("tests", "**", "*.yaml"), recursive=True):
                paths_to_lint_yaml.append("tests")

        file_content = []

        template_data = self._GenerateFromTemplate("header.yml", template_mappings)
        file_content.append(template_data)

        if paths_to_lint_yaml and self._project_definition.name != "l2tdevtools":
            template_data = self._GenerateFromTemplate(
                "yamllint.yml", template_mappings
            )
            file_content.append(template_data)

        file_content = "".join(file_content)

        with open(self.PATH, "w", encoding="utf-8") as file_object:
            file_object.write(file_content)


class GitHubActionsTestDockerYmlWriter(interface.DependencyFileWriter):
    """test_docker.yml GitHub actions workflow file writer."""

    _TEMPLATE_FILE = os.path.join(
        "data", "templates", "github_actions", "test_docker.yml"
    )

    PATH = os.path.join(".github", "workflows", "test_docker.yml")

    def Write(self):
        """Writes a test_docker.yml GitHub actions workflow file ."""
        dpkg_dependencies = self._GetDPKGPythonDependencies()
        test_dependencies = self._GetDPKGTestDependencies(dpkg_dependencies)
        dpkg_dependencies.extend(test_dependencies)
        dpkg_dependencies.extend(
            [
                "python3",
                "python3-build",
                "python3-dev",
                "python3-pip",
                "python3-setuptools",
                "python3-venv",
                "python3-wheel",
            ]
        )

        rpm_dependencies = self._GetRPMPythonDependencies()
        test_dependencies = self._GetRPMTestDependencies(rpm_dependencies)
        rpm_dependencies.extend(test_dependencies)
        rpm_dependencies.extend(
            [
                "python3",
                "python3-build",
                "python3-devel",
                "python3-setuptools",
                "python3-wheel",
            ]
        )

        template_mappings = {
            "dpkg_dependencies": " ".join(sorted(set(dpkg_dependencies))),
            "rpm_dependencies": " ".join(sorted(set(rpm_dependencies))),
        }

        template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
        file_content = self._GenerateFromTemplate(template_file, template_mappings)

        with open(self.PATH, "w", encoding="utf-8") as file_object:
            file_object.write(file_content)


class GitHubActionsTestDocsYmlWriter(interface.DependencyFileWriter):
    """test_docs.yml GitHub actions workflow file writer."""

    _TEMPLATE_FILE = os.path.join(
        "data", "templates", "github_actions", "test_docs.yml"
    )

    PATH = os.path.join(".github", "workflows", "test_docs.yml")

    def Write(self):
        """Writes a test_docs.yml GitHub actions workflow file ."""
        dpkg_dependencies = self._GetDPKGPythonDependencies()
        test_dependencies = self._GetDPKGTestDependencies(dpkg_dependencies)
        dpkg_dependencies.extend(test_dependencies)
        dpkg_dependencies.extend(["python3-pip", "python3-setuptools", "tox"])

        dpkg_dev_dependencies = self._GetDPKGDevDependencies()

        template_mappings = {
            "dpkg_dependencies": " ".join(sorted(set(dpkg_dependencies))),
            "dpkg_dev_dependencies": " ".join(sorted(set(dpkg_dev_dependencies))),
        }

        template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
        file_content = self._GenerateFromTemplate(template_file, template_mappings)

        with open(self.PATH, "w", encoding="utf-8") as file_object:
            file_object.write(file_content)


class GitHubActionsTestMacOSYmlWriter(interface.DependencyFileWriter):
    """test_macos.yml GitHub actions workflow file writer."""

    _TEMPLATE_FILE = os.path.join(
        "data", "templates", "github_actions", "test_macos.yml"
    )

    PATH = os.path.join(".github", "workflows", "test_macos.yml")

    def Write(self):
        """Writes a test_macos.yml GitHub actions workflow file ."""
        template_mappings = {}

        template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
        file_content = self._GenerateFromTemplate(template_file, template_mappings)

        with open(self.PATH, "w", encoding="utf-8") as file_object:
            file_object.write(file_content)


class GitHubActionsTestToxYmlWriter(interface.DependencyFileWriter):
    """test_tox.yml GitHub actions workflow file writer."""

    _TEMPLATE_FILE = os.path.join("data", "templates", "github_actions", "test_tox.yml")

    PATH = os.path.join(".github", "workflows", "test_tox.yml")

    def Write(self):
        """Writes a test_tox.yml GitHub actions workflow file ."""
        dpkg_dependencies = self._GetDPKGPythonDependencies()
        test_dependencies = self._GetDPKGTestDependencies(dpkg_dependencies)
        dpkg_dependencies.extend(test_dependencies)
        dpkg_dependencies.extend(["python3-pip", "python3-setuptools", "tox"])

        dpkg_dev_dependencies = self._GetDPKGDevDependencies()

        template_mappings = {
            "dpkg_dependencies": " ".join(sorted(set(dpkg_dependencies))),
            "dpkg_dev_dependencies": " ".join(sorted(set(dpkg_dev_dependencies))),
        }

        template_file = os.path.join(self._l2tdevtools_path, self._TEMPLATE_FILE)
        file_content = self._GenerateFromTemplate(template_file, template_mappings)

        with open(self.PATH, "w", encoding="utf-8") as file_object:
            file_object.write(file_content)
