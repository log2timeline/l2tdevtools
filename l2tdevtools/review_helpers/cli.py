# -*- coding: utf-8 -*-
"""Helper for command line functions."""

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

    Raises:
      AttributeError: if the command is not recognized.
    """
    if self.mock_responses:
      return_values = self.mock_responses.get(command, None)
      if not return_values:
        raise AttributeError('Unrecognized command.')
      return return_values

    arguments = shlex.split(command)

    exit_code = 1
    output = None
    error = None

    try:
      with subprocess.Popen(
          arguments, stderr=subprocess.PIPE, stdout=subprocess.PIPE) as process:
        output, error = process.communicate()
        output = codecs.decode(output, self.preferred_encoding)
        error = codecs.decode(error, self.preferred_encoding)
        exit_code = process.returncode
        if exit_code != 0:
          logging.error('Running: "{0:s}" failed with error: {1!s}.'.format(
              command, error))

    except OSError as exception:
      logging.error('Running: "{0:s}" failed with error: {1!s}'.format(
          command, exception))

    return exit_code, output, error
