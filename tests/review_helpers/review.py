#!/usr/bin/env python3
"""Tests for the review helper."""

import os
import sys
import unittest
from unittest import mock

from l2tdevtools.review_helpers import review

from tests import test_lib


class ReviewHelperTest(test_lib.BaseTestCase):
    """Tests the review helper."""

    def testInitialize(self):
        """Tests that the helper can be initialized."""
        helper = review.ReviewHelper(
            "test",
            ".",
            "https://github.com/log2timeline/l2tdevtools.git",
            "import",
            "upstream/main",
        )
        self.assertIsNotNone(helper)

    @mock.patch("l2tdevtools.review_helpers.review.subprocess.call")
    def testTestChangedFiles(self, mock_subprocess_call):
        """Tests running tests selected from changed files."""
        mock_subprocess_call.return_value = 0

        project_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        helper = review.ReviewHelper("test", project_path, None, None)
        helper._project_name = "l2tdevtools"
        helper._git_helper = mock.Mock()

        helper._git_helper.GetChangedFiles.return_value = [
            "l2tdevtools/review_helpers/review.py"
        ]
        self.assertTrue(helper.Test())
        mock_subprocess_call.assert_called_once_with(
            [sys.executable, "-m", "unittest", "tests.review_helpers.review"]
        )

        helper._project_name = "dfvfs"
        helper._git_helper.GetChangedFiles.return_value = [
            "dfvfs/review_helpers/review.py"
        ]
        mock_subprocess_call.reset_mock()
        self.assertTrue(helper.Test())
        mock_subprocess_call.assert_called_once_with(
            [sys.executable, "-m", "unittest", "tests.review_helpers.review"]
        )

        helper._git_helper.GetChangedFiles.return_value = ["README.md"]
        mock_subprocess_call.reset_mock()
        self.assertTrue(helper.Test())
        mock_subprocess_call.assert_not_called()

        helper._git_helper.GetChangedFiles.return_value = ["pyproject.toml"]
        self.assertTrue(helper.Test())
        mock_subprocess_call.assert_called_once_with([sys.executable, "run_tests.py"])

        helper._all_files = True
        mock_subprocess_call.reset_mock()
        self.assertTrue(helper.Test())
        mock_subprocess_call.assert_called_once_with([sys.executable, "run_tests.py"])

    # TODO: test CheckLocalGitState.
    # TODO: test CheckRemoteGitState.
    # TODO: test Close.
    # TODO: test CreatePullRequest.
    # TODO: test InitializeHelpers.
    # TODO: test Lint.
    # TODO: test Merge.
    # TODO: test PrepareUpdate.
    # TODO: test PullChangesFromFork.
    # TODO: test Test.
    # TODO: test UpdateAuthors.
    # TODO: test UpdateVersion.


if __name__ == "__main__":
    unittest.main()
