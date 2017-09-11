# -*- coding: utf-8 -*-
"""Implementation of a net resources file."""
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

    home_path = os.path.expanduser(u'~')
    self._path = os.path.join(home_path, u'.netrc')
    if not os.path.exists(self._path):
      return

    with open(self._path, 'r') as file_object:
      self._contents = file_object.read()

  def _GetGitHubValues(self):
    """Retrieves the github values.

    Returns:
      list[str]: .netrc values for github.com or None.
    """
    if not self._contents:
      return

    # Note that according to GNU's manual on .netrc file, the credential
    # tokens "may be separated by spaces, tabs, or new-lines".
    if not self._values:
      self._values = self._NETRC_SEPARATOR_RE.findall(self._contents)

    for value_index, value in enumerate(self._values):
      if value == u'github.com' and self._values[value_index - 1] == u'machine':
        return self._values[value_index + 1:]

  def GetGitHubAccessToken(self):
    """Retrieves the github access token.

    Returns:
      str: github access token or None.
    """
    values = self._GetGitHubValues()
    if not values:
      return

    for value_index, value in enumerate(values):
      if value == u'password':
        return values[value_index + 1]

  def GetGitHubUsername(self):
    """Retrieves the github username.

    Returns:
      str: github username or None.
    """
    values = self._GetGitHubValues()
    if not values:
      return

    login_value = None
    for value_index, value in enumerate(values):
      if value == u'login':
        login_value = values[value_index + 1]

      # If the next field is 'password' we assume the login field is empty.
      if login_value != u'password':
        return login_value
