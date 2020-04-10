"""
Functions to help interact with strings.
"""
import logging
import re
from pathlib import Path


def remove_from_start_if_present(target, start):
    """Remove substring from the beginning of a string.

    Removes a substring if it is part of the beginning of the given string.

    :param target:  String to modify
    :type target:   str
    :param start:   Substring to remove, if it exists.
    :return:
    """
    if target and target.startswith(start):
        return ''.join(target[len(start):])
    return target


def given_version_is_newer(original_version, new_version):
    """Determine if a new version string is newer than the original version string.

    Given a version string, determine whether or not it's newer than the compare
    version given.

    :param original_version:    Version string to compare
    :type original_version:     str
    :param new_version:         Version string to compare against
    :type new_version:          str
    :return:                    True if the given version is newer than the compare one, else False
    :rtype:                     bool
    """
    orig_version_parts = [int(x) for x in original_version.replace('-', '.').split('.')]
    new_version_parts = [int(x) for x in new_version.replace('-', '.').split('.')]

    return new_version_parts > orig_version_parts


def sed(file_path, search_pattern, replace_string):
    """VERY simple Python implementation of sed.

    Does a basic string replacement in a file based on a given search pattern
    and replacement string. Don't expect it to work like Bash sed! Works using
    Pythons regex library `re.sub` function.

    :param file_path:       Path to the file to edit
    :type file_path:        str or Path
    :param search_pattern:  Regex pattern used for locating the string to replace
    :type search_pattern:   str
    :param replace_string:  String to replace when a match occurs
    :type replace_string:   str
    :return:                0 for success, 1 for failure
    """
    if isinstance(file_path, str):
        edit_file = Path(file_path)
    else:
        edit_file = file_path

    search_pattern = re.compile(rf'{search_pattern}')

    if not edit_file.exists():
        logging.error(f'Given file path {file_path} does not exist')
        return 1

    with open(edit_file, 'r') as read_file:
        file_contents = read_file.readlines()

    with open(edit_file, 'w') as write_file:
        for line in file_contents:
            write_file.write(re.sub(search_pattern, replace_string, line))

    return 0
