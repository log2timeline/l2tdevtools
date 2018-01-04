# -*- coding: utf-8 -*-
"""Functions to handle package versions."""


def CompareVersions(first_version_list, second_version_list):
  """Compares two lists containing version parts.

  Note that the version parts can contain alpha numeric characters.

  Args:
    first_version_list (list[str]): first version parts.
    second_version_list (list[str]): second version parts.

  Returns:
    int: 1 if the first is larger than the second, -1 if the first is smaller
        than the second, or 0 if the first and second are equal.
  """
  first_version_list_length = len(first_version_list)
  second_version_list_length = len(second_version_list)

  for index in range(0, first_version_list_length):
    if index >= second_version_list_length:
      return 1

    try:
      first_version_part = int(first_version_list[index], 10)
      second_version_part = int(second_version_list[index], 10)
    except ValueError:
      first_version_part = first_version_list[index]
      second_version_part = second_version_list[index]

    if first_version_part > second_version_part:
      return 1
    elif first_version_part < second_version_part:
      return -1

  if first_version_list_length < second_version_list_length:
    return -1

  return 0
