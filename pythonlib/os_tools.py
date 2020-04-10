"""
Common module used for OS level helper functions
"""
from .__init__ import *


def create_parent_dirs(file_path):
    """Directory tree creation function

    Creates a directory structure given a file path, with parents created if necessary

    :param file_path    The path or file path to create directories for
    :type file_path     Path
    :return:            0 for success, 1 for failure.
    """
    parent_path = Path(file_path.absolute()).parent
    parent_path.mkdir(parents=True, exist_ok=True)


def make_symlink(from_path, to_path, log_domain=''):
    """Directory tree creation function

    Creates a symlink given a path to place the symlink, and a target file/folder for the symlink.  Also creates any
    needed parent folders for the symlink

    :param from_path:   The path where the symlink will be placed
    :type from_path:    Path
    :param to_path:     The path that the symlink will be pointing to (file or folder)
    :type to_path:      Path
    :param log_domain:  Specify a log domain to send logging output to.
    :type log_domain:   str
    :return:            0 for success, 1 for failure.
    """
    log = logging.getLogger(log_domain)
    if from_path.exists():
        log.debug(f'Destination file exists; removing {from_path}')
        log.debug('Removing directory') if Path(from_path).is_dir() else log.info('Removing file or symlink')
        is_file_or_link = Path(from_path).is_file() or Path(from_path).is_symlink()
        from_path.unlink() if is_file_or_link else shutil.rmtree(from_path)

    create_parent_dirs(from_path)
    from_path.symlink_to(to_path)
    log.info(f'Symlink created from {from_path} to {to_path}')
