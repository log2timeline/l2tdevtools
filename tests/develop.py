#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the docker development environment management tool."""

from __future__ import unicode_literals

import unittest
from unittest.mock import patch, Mock

from tools import develop

from tests import test_lib

class DockerDevelopmentEnvironmentTest(test_lib.BaseTestCase):
  """Tests for the docker development environment management tool."""

  @patch('develop.Repo')
  def testBuildDevImage(self, mockRepo):
    repo = mockRepo()
    repo.return_value = Mock(
      head=Mock(
        commit="abcde"
      )
    )

if __name__ == '__main__':
  unittest.main()
