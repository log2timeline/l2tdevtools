# -*- coding: utf-8 -*-
"""Implementation of a net resources file."""
from __future__ import unicode_literals

import os
import re


class NetRCFile(object):
  """Net resources (.netrc) file."""

  _NETRC_SEPARATOR_RE = re.compile(r'[^ \t\n]+')

  def __init__(self):
    """Initializes a .netrc file."""
    super(NetRCFile, self).__init__()
    self._contents = None
    self._values = None

    home_path = os.path.expanduser('~')
    self._path = os.path.join(home_path, '.netrc')
    if not os.path.exists(self._path):
      return

    with open(self._path, 'r') as file_object:
      self._contents = file_object.read()

  def _GetGitHubValues(self):
    """Retrieves the GitHub values.

    Returns:
      list[str]: .netrc values for github.com or None.
    """
    if self._contents:
      # Note that according to GNU's manual on .netrc file, the credential
      # tokens "may be separated by spaces, tabs, or new-lines".
      if not self._values:
        self._values = self._NETRC_SEPARATOR_RE.findall(self._contents)

      for value_index, value in enumerate(self._values):
        if value == 'github.com' and self._values[value_index - 1] == 'machine':
          return self._values[value_index + 1:]

    return None

  def GetGitHubAccessToken(self):
    """Retrieves the GitHub access token.

    Returns:
      str: GitHub access token or None.
    """
    values = self._GetGitHubValues()
    if not values:
      return None

    for value_index, value in enumerate(values):
      if value == 'password':
        return values[value_index + 1]

    return None

  def GetGitHubUsername(self):
    """Retrieves the GitHub username.

    Returns:
      str: GitHub username or None.
    """
    values = self._GetGitHubValues()
    if not values:
      return None

    login_value = None
    for value_index, value in enumerate(values):
      if value == 'login':
        login_value = values[value_index + 1]

      # If the next field is 'password' we assume the login field is empty.
      if login_value != 'password':
        return login_value

    return None
