# -*- coding: utf-8 -*-
"""Helper for command line functions."""
import logging
import shlex
import subprocess


class CLIHelper(object):
  """Command line interface (CLI) helper."""

  def __init__(self, mock_responses=None):
    """Initializes a CLI helper.

    Args:
      mock_responses(Optional[dict[str, str]): dict mapping commands to
          responses, used for testing.
    """
    super(CLIHelper, self).__init__()
    self.mock_responses = mock_responses

  def RunCommand(self, command):
    """Runs a command.

    Args:
      command (str): command to run.

    Returns:
      tuple[int, bytes, bytes]: exit code, stdout and stderr data.
    """
    if self.mock_responses:
      return_values = self.mock_responses.get(command, None)
      if not return_values:
        raise AttributeError(u'Unrecognized command.')
      return return_values

    arguments = shlex.split(command)

    try:
      process = subprocess.Popen(
          arguments, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    except OSError as exception:
      logging.error(
          u'Running: "{0:s}" failed with error: {1:s}'.format(
              command, exception))
      return 1, None, None

    output, error = process.communicate()
    if process.returncode != 0:
      logging.error(
          u'Running: "{0:s}" failed with error: {1!s}.'.format(command, error))

    return process.returncode, output, error
