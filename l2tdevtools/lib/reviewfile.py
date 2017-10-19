# -*- coding: utf-8 -*-
"""Implementation of a file to store code review information."""
from __future__ import unicode_literals

import os


class ReviewFile(object):
  """Defines a review file.

  A review file is used to track code review relevant information like the
  codereview issue number. It is stored in the .review subdirectory and
  named after the feature branch e.g. ".review/feature".
  """

  def __init__(self, branch_name):
    """Initializes a review file.

    Args:
      branch_name (str): name of the feature branch of the review.
    """
    super(ReviewFile, self).__init__()
    self._contents = None
    self._path = os.path.join('.review', branch_name)

    if os.path.exists(self._path):
      with open(self._path, 'r') as file_object:
        self._contents = file_object.read()

  def Create(self, codereview_issue_number):
    """Creates a new review file.

    If the .review directory does not exist, it will be created.

    Args:
      codereview_issue_number (int|str): codereview issue number.

    Returns:
      bool: True if the review file was created.
    """
    if not os.path.exists('.review'):
      os.mkdir('.review')
    with open(self._path, 'w') as file_object:
      file_object.write('{0!s}'.format(codereview_issue_number))

  def Exists(self):
    """Determines if the review file exists.

    Returns:
      bool: True if review file exists.
    """
    return os.path.exists(self._path)

  def GetCodeReviewIssueNumber(self):
    """Retrieves the codereview issue number.

    Returns:
      int: codereview issue number.
    """
    if not self._contents:
      return

    try:
      return int(self._contents, 10)
    except ValueError:
      pass

  def Remove(self):
    """Removes the review file."""
    if not os.path.exists(self._path):
      return

    os.remove(self._path)
