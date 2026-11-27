#!/usr/bin/env python3
"""Tests for the tox.ini writer."""

import os
import unittest

from l2tdevtools import dependencies
from l2tdevtools import project_config
from l2tdevtools.dependency_writers import tox_ini
from l2tdevtools.helpers import project
from tests import test_lib


class ToxIniWriterTest(test_lib.BaseTestCase):
    """Tests the tox.ini writer."""

    def testInitialize(self):
        """Tests that the writer can be initialized."""
        l2tdevtools_path = "/fake/l2tdevtools/"
        project_definition = project.ProjectHelper(l2tdevtools_path)
        dependencies_file = self._GetTestFilePath(["dependencies.ini"])
        test_dependencies_file = self._GetTestFilePath(["test_dependencies.ini"])
        dependency_helper = dependencies.DependencyHelper(
            dependencies_file=dependencies_file,
            test_dependencies_file=test_dependencies_file,
        )

        writer = tox_ini.ToxIniWriter(
            l2tdevtools_path, project_definition, dependency_helper
        )
        self.assertIsNotNone(writer)

    def testWrite(self):
        """Tests the Write function."""
        l2tdevtools_path = os.getcwd()
        project_definition = project_config.ProjectDefinition()
        project_definition.name = "test"
        dependencies_file = self._GetTestFilePath(["dependencies.ini"])
        test_dependencies_file = self._GetTestFilePath(["test_dependencies.ini"])
        dependency_helper = dependencies.DependencyHelper(
            dependencies_file=dependencies_file,
            test_dependencies_file=test_dependencies_file,
        )

        writer = tox_ini.ToxIniWriter(
            l2tdevtools_path, project_definition, dependency_helper
        )

        with test_lib.TempDirectory() as temp_directory:
            os.mkdir(os.path.join(temp_directory, "benchmarks"))
            os.mkdir(os.path.join(temp_directory, "tests"))

            current_working_directory = os.getcwd()
            os.chdir(temp_directory)

            try:
                writer.Write()
            finally:
                os.chdir(current_working_directory)

            tox_ini_path = os.path.join(temp_directory, "tox.ini")
            with open(tox_ini_path, encoding="utf-8") as file_object:
                file_content = file_object.read()

        self.assertIn(
            (
                "  coverage: coverage\n"
                "  coverage: pbr >= 4.2.0\n"
                "  py3{10,11,12,13,14,15}: pbr >= 4.2.0\n"
                "  wheel:\n"
            ),
            file_content,
        )
        self.assertIn(
            (
                "[testenv:benchmark]\n"
                "deps =\n"
                "  pbr >= 4.2.0\n"
                "  pytest-benchmark\n"
                "commands =\n"
                "  python -m pytest benchmarks\n"
            ),
            file_content,
        )
        self.assertIn("  pylint --rcfile=.pylintrc benchmarks tests\n", file_content)


if __name__ == "__main__":
    unittest.main()
