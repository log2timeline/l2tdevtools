"""Helper for interacting with a project."""

import logging
import os
import tomllib

from l2tdevtools import project_config
from l2tdevtools.review_helpers import cli


class ProjectHelper(cli.CLIHelper):
    """Helper for interacting with a project.

    Attributes:
      project_name (str): name of the project.
    """

    _AUTHORS_FILE_HEADER = [
        "# Names should be added to this file with this pattern:",
        "#",
        "# For individuals:",
        "#   Name (email address)",
        "#",
        "# For organizations:",
        "#   Organization (fnmatch pattern)",
        "#",
        "# See python fnmatch module documentation for more information.",
        "",
        "Google Inc. (*@google.com)",
    ]

    SUPPORTED_PROJECTS = frozenset(
        [
            "acstore",
            "artifacts",
            "artifacts-kb",
            "clitooltester",
            "dfdatetime",
            "dfkinds",
            "dfimagetools",
            "dftimewolf",
            "dfvfs",
            "dfvfs-snippets",
            "dfwinreg",
            "dtfabric",
            "dtformats",
            "esedb-kb",
            "l2tdevtools",
            "l2tdocs",
            "l2tscaffolder",
            "olecf-kb",
            "plaso",
            "plist-kb",
            "sqlite-kb",
            "vstools",
            "winevt-kb",
            "winreg-kb",
            "winshl-kb",
            "winsps-kb",
        ]
    )

    def __init__(self, project_path):
        """Initializes a project helper.

        Args:
          project_path (str): path to the project.

        Raises:
          ValueError: if the project name is not supported.
        """
        super().__init__()
        self._project_definition = None
        self.project_name = self._GetProjectName(project_path)

    @property
    def version_file_path(self):
        """str: path of the version file."""
        return os.path.join(self.project_name, "__init__.py")

    def _GetProjectName(self, project_path):
        """Retrieves the project name from the script path.

        Args:
          project_path (str): path to the root of the project.

        Returns:
          str: project name.

        Raises:
          ValueError: if the project name is not supported.
        """
        project_name = os.path.abspath(project_path)
        project_name = os.path.basename(project_name)

        # The review.py check is needed for the l2tdevtools tests.
        if project_name != "review.py" and project_name not in self.SUPPORTED_PROJECTS:
            raise ValueError(f"Unsupported project name: {project_name:s}.")

        return project_name

    def _ReadFileContents(self, path):
        """Reads the contents of a file.

        Args:
          path (str): path of the file.

        Returns:
          bytes: file content or None if not available.
        """
        if not os.path.exists(path):
            logging.error(f"Missing file: {path:s}")
            return None

        try:
            with open(path, "rb") as file_object:
                file_contents = file_object.read()

        except IOError as exception:
            logging.error(f"Unable to read file with error: {exception!s}")
            return None

        try:
            file_contents = file_contents.decode("utf-8")
        except UnicodeDecodeError as exception:
            logging.error(f"Unable to read file with error: {exception!s}")
            return None

        return file_contents

    def ReadDefinitionFile(self):
        """Reads the project definitions file (project_name.ini).

        Returns:
          ProjectDefinition: project definition.
        """
        if self._project_definition is None:
            project_ini = f"{self.project_name:s}.ini"

            if os.path.isfile(project_ini):
                logging.warning(
                    f"{project_ini:s} has been deprecated consider migrating to "
                    f"pyproject.toml [tool.l2tdevtools]"
                )
                project_reader = project_config.ProjectDefinitionReader()
                with open(
                    f"{self.project_name:s}.ini", encoding="utf-8"
                ) as file_object:
                    self._project_definition = project_reader.Read(file_object)

            else:
                with open("pyproject.toml", "rb") as file_object:
                    pyproject_toml = tomllib.load(file_object)

                project = pyproject_toml.get("project", {})
                project_urls = project.get("urls", {})
                tool = pyproject_toml.get("tool", {})
                tool_l2tdevtools = tool.get("l2tdevtools", {})

                maintainer = None
                maintainers = project.get("maintainers", [])
                if maintainers:
                    maintainer = maintainers[0]
                    maintainer = f'{maintainer["name"]:s} <{maintainer["email"]:s}>'

                git_url = project_urls.get("Repository")
                if git_url:
                    git_url = f"{git_url:s}.git"

                project_definition = project_config.ProjectDefinition()
                project_definition.description_long = tool_l2tdevtools.get(
                    "description"
                ).rstrip()
                project_definition.description_short = project.get("description")
                project_definition.git_url = git_url
                project_definition.homepage_url = project_urls.get("Homepage")
                project_definition.maintainer = maintainer
                project_definition.name = project.get("name")
                project_definition.name_description = tool_l2tdevtools.get("name")
                project_definition.status = tool_l2tdevtools.get("status")

                self._project_definition = project_definition

        return self._project_definition
