# -*- coding: utf-8 -*-
"""Helper for command line functions."""

from __future__ import unicode_literals

import codecs
import locale
import logging
import shlex
import subprocess


class CLIHelper(object):
  """Command line interface (CLI) helper.

  Attributes:
    mock_responses (dict[str, str]): mappings of commands to responses.
    preferred_encoding (str): preferred encoding of output.
  """

  def __init__(self, mock_responses=None):
    """Initializes a CLI helper.

    Args:
      mock_responses (Optional[dict[str, str]]): mappings of commands to
          responses, for testing.
    """
    super(CLIHelper, self).__init__()
    self.mock_responses = mock_responses
    self.preferred_encoding = locale.getpreferredencoding()

  def RunCommand(self, command):
    """Runs a command.

    Args:
      command (str): command to run.

    Returns:
      tuple[int, str, str]: exit code, output that was written to stdout
          and stderr.
    """
    if self.mock_responses:
      return_values = self.mock_responses.get(command, None)
      if not return_values:
        raise AttributeError('Unrecognized command.')
      return return_values

    arguments = shlex.split(command)

    try:
      process = subprocess.Popen(
          arguments, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    except OSError as exception:
      logging.error(
          'Running: "{0:s}" failed with error: {1!s}'.format(
              command, exception))
      return 1, None, None

    output, error = process.communicate()
    output = codecs.decode(output, self.preferred_encoding)
    error = codecs.decode(error, self.preferred_encoding)
    if process.returncode != 0:
      logging.error(
          'Running: "{0:s}" failed with error: {1!s}.'.format(command, error))

    return process.returncode, output, error
