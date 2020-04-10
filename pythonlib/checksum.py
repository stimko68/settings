"""
Common module for functions that deal with checksums
"""
from .__init__ import *


def generate_checksum(file_path, checksum_type, output_filename=None, skip_files=None):
    """Generate a checksum for a given file or directory.

    Given a file path (it can be relative) and a checksum type, generate
    a checksum and return it. If an output filename is given then the checksum
    will be saved to the file. This function can also generate a checksum for
    a given directory by generating a combined checksum of everything in the
    directory.

    :param file_path:       Location of the file or directory to be checksummed
    :type file_path:        str
    :param checksum_type:   Algorithm to use when calculating the checksum
                            (e.g., md5, sha1, sha256, etc).
    :type checksum_type:    str
    :param output_filename: (optional) Location of the output file where the
                            checksum string and filename of the checksummed
                            file should be saved. If the `file_path` is a directory,
                            then the name of the directory is used.
    :type output_filename:  str
    :param skip_files:      (optional) If requesting the checksum for an entire directory,
                            you can pass a list of files to skip when generating the checksum.
    :type skip_files:       list
    :return:                Checksum for the given file/directory
    :rtype:                 str
    """
    file_path = os.path.abspath(file_path)

    if skip_files is None:
        skip_files = list()

    if type(skip_files) != list:
        error = f'`skip_files` must be a list'
        logging.error(error)
        raise TypeError(error)

    if not os.path.exists(file_path):
        error = f'The given file does not exist or you do not have permission to access it: {file_path}'
        logging.error(error)
        raise OSError(error)

    # Get the hash object
    try:
        hash_obj = getattr(hashlib, checksum_type)()
    except AttributeError:
        error = f'{checksum_type} is not a valid checksum type'
        logging.error(error)
        raise AttributeError(error)

    if os.path.isdir(file_path):
        for root, dirs, files in os.walk(file_path):
            for f in files:
                if not os.path.isdir(f) and f not in skip_files:
                    check_file = os.path.join(root, f)
                    file_size = os.path.getsize(check_file)

                    if file_size < 1024:
                        block_size = file_size
                    else:
                        block_size = 1024

                    with open(check_file, 'rb') as c_file:
                        while True:
                            buffer = c_file.read(block_size)

                            if not buffer:
                                break

                            hash_obj.update(buffer)
    else:
        # Read the file in chunks so we don't fill up the system's memory
        file_size = os.path.getsize(file_path)

        if file_size < 1024:
            block_size = file_size
        else:
            block_size = 1024

        with open(file_path, 'rb') as c_file:
            while True:
                buffer = c_file.read(block_size)

                if not buffer:
                    break

                hash_obj.update(buffer)

    checksum = hash_obj.hexdigest()

    if output_filename:
        output_filename = os.path.abspath(output_filename)

        with open(output_filename, 'w') as o_file:
            o_file.write(f'{checksum} {file_path}')

    return checksum
