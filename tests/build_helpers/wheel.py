#!/usr/bin/env python3
"""Tests for the helper for building projects from source."""

import os
import shutil
import unittest

from l2tdevtools import projects
from l2tdevtools.build_helpers import wheel

from tests import test_lib as shared_test_lib
from tests.build_helpers import test_lib


class WheelBuildHelperTest(shared_test_lib.BaseTestCase):
    """Tests for the helper to build Python wheel packages (.whl)."""

    # pylint: disable=protected-access

    _TEST_PROJECT_NAME = "dfdatetime"
    _TEST_PROJECT_VERSION = "20190517"

    def testInitialize(self):
        """Tests the __init__ function."""
        project_definition = projects.ProjectDefinition("test")

        l2tdevtools_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        test_build_helper = wheel.WheelBuildHelper(
            project_definition, l2tdevtools_path, {}
        )
        self.assertIsNotNone(test_build_helper)

    def testGetWheelFilenameProjectInformation(self):
        """Tests the _GetWheelFilenameProjectInformation function."""
        project_definition = projects.ProjectDefinition(self._TEST_PROJECT_NAME)

        l2tdevtools_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        test_build_helper = wheel.WheelBuildHelper(
            project_definition, l2tdevtools_path, {}
        )

        source_helper_object = test_lib.TestSourceHelper(
            self._TEST_PROJECT_NAME, project_definition, self._TEST_PROJECT_VERSION
        )

        project_name, project_version = (
            test_build_helper._GetWheelFilenameProjectInformation(source_helper_object)
        )
        self.assertEqual(project_name, self._TEST_PROJECT_NAME)
        self.assertEqual(project_version, self._TEST_PROJECT_VERSION)

    # TODO: add tests for _MoveWheel

    def testCheckBuildDependencies(self):
        """Tests the CheckBuildDependencies function."""
        project_definition = projects.ProjectDefinition(self._TEST_PROJECT_NAME)
        project_definition.build_dependencies = []

        l2tdevtools_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        test_build_helper = wheel.WheelBuildHelper(
            project_definition, l2tdevtools_path, {}
        )

        missing_packages = test_build_helper.CheckBuildDependencies()
        self.assertEqual(missing_packages, [])

    def testCheckBuildRequired(self):
        """Tests the CheckBuildRequired function."""
        project_definition = projects.ProjectDefinition(self._TEST_PROJECT_NAME)
        project_definition.build_dependencies = []

        l2tdevtools_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        test_build_helper = wheel.WheelBuildHelper(
            project_definition, l2tdevtools_path, {}
        )

        source_helper_object = test_lib.TestSourceHelper(
            self._TEST_PROJECT_NAME, project_definition, self._TEST_PROJECT_VERSION
        )

        result = test_build_helper.CheckBuildRequired(source_helper_object)
        self.assertTrue(result)

    def testClean(self):
        """Tests the Clean function."""
        project_definition = projects.ProjectDefinition(self._TEST_PROJECT_NAME)
        project_definition.build_dependencies = []

        l2tdevtools_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        test_build_helper = wheel.WheelBuildHelper(
            project_definition, l2tdevtools_path, {}
        )

        source_helper_object = test_lib.TestSourceHelper(
            self._TEST_PROJECT_NAME, project_definition, self._TEST_PROJECT_VERSION
        )

        with shared_test_lib.TempDirectory() as temp_directory:
            test_filename = f"{self._TEST_PROJECT_NAME:s}-20180101-py3-none-any.whl"
            test_path = os.path.join(temp_directory, test_filename)

            with open(test_path, "a", encoding="utf-8"):
                pass

            test_wheel_filename = (
                f"{self._TEST_PROJECT_NAME:s}-{self._TEST_PROJECT_VERSION:s}-py3-"
                f"none-any.whl"
            )

            test_path = os.path.join(temp_directory, test_wheel_filename)
            with open(test_path, "a", encoding="utf-8"):
                pass

            directory_entries = os.listdir(temp_directory)
            self.assertEqual(len(directory_entries), 2)

            current_working_directory = os.getcwd()
            os.chdir(temp_directory)

            try:
                test_build_helper.Clean(source_helper_object)
            finally:
                os.chdir(current_working_directory)

            directory_entries = os.listdir(temp_directory)
            self.assertEqual(len(directory_entries), 1)
            self.assertIn(test_wheel_filename, directory_entries)


class ConfigureMakeWheelBuildHelperTest(shared_test_lib.BaseTestCase):
    """Tests for the helper to build Python wheel packages (.whl)."""

    _TEST_PROJECT_NAME = "libsigscan"
    _TEST_PROJECT_VERSION = "20231201"

    def testBuild(self):
        """Tests the Build function."""
        project_definition = projects.ProjectDefinition(self._TEST_PROJECT_NAME)
        project_definition.build_dependencies = []
        project_definition.wheel_name = "libsigscan_python"

        l2tdevtools_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        test_build_helper = wheel.ConfigureMakeWheelBuildHelper(
            project_definition, l2tdevtools_path, {}
        )

        source_helper_object = test_lib.TestSourceHelper(
            self._TEST_PROJECT_NAME, project_definition, self._TEST_PROJECT_VERSION
        )

        with shared_test_lib.TempDirectory() as temp_directory:
            test_filename = (
                f"{self._TEST_PROJECT_NAME:s}-{self._TEST_PROJECT_VERSION:s}.tar.gz"
            )
            test_path = os.path.join(l2tdevtools_path, "test_data", test_filename)

            shutil.copy(test_path, temp_directory)

            directory_entries = os.listdir(temp_directory)
            self.assertEqual(len(directory_entries), 1)

            current_working_directory = os.getcwd()
            os.chdir(temp_directory)

            try:
                source_helper_object.Create()
                test_build_helper.Build(source_helper_object)
            finally:
                os.chdir(current_working_directory)

            directory_entries = os.listdir(temp_directory)
            self.assertIn("build.log", directory_entries)

            if len(directory_entries) < 4:
                build_log_path = os.path.join(temp_directory, "build.log")
                with open(build_log_path, "r", encoding="utf-8") as file_object:
                    print("".join(file_object.readlines()))

            self.assertEqual(len(directory_entries), 4)


if __name__ == "__main__":
    unittest.main()
