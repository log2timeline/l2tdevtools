# -*- coding: utf-8 -*-
"""Test case to have linter fail."""


class LinterFailTestClass(object):
  """Linter fail test class."""

  def __init__(self):
    """Initializes a linter fail test object."""
    super(LinterFailTestClass, self).__init__()
    # Note that the indentation here is deliberately broken.
     self._attribute = None
