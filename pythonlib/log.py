"""
Common logging functions used across all modules.
"""
import logging
import os


def setup_logging(log_domain, stream=True, logfile=None, log_level='info'):
    """Sets up logging using the given log domain.

    Set up a logging object using a log domain name with various options. The default is to
    create a stream logger (i.e., stream output to the terminal), but the logger
    can be setup to output to a logfile as well.

    To output the logging data to a logfile, provide a filename to the `logfile`
    parameter. If no path is provided then the logfile will be created in the
    current directory. If a path is provided then the logfile will be created
    in the specific location.

    When specifying a log domain, use a unique name. If you specify the name
    of a log domain that already exists, you will be given the log object that
    was setup with that log domain. This can be useful if you are running multiple
    scripts which need to write to the same logfile.

    :param log_domain:  Name of the logger
    :type log_domain:   str
    :param stream:      (optional) Sets up the logging to stream to the console.
                        Defaults to `True`.
    :param logfile:     (optional) Outputs the logging to a file. Can provide a
                        filename only or a path to a filename.
    :param log_level:   (optional) What log level to output. Default is INFO.
                        Other options include DEBUG, CRITICAL, ERROR, and
    :return:            Logging object with desired options.
    :rtype:             `logging.logger`
    """
    logger = logging.getLogger(log_domain)

    if not logger.handlers:
        # Only configure the logger if it has no handlers
        logger.setLevel(getattr(logging, log_level.upper()))

        log_format = logging.Formatter('%(asctime)s [%(module)s] [%(levelname)s]: %(message)s')

        if stream:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(log_format)
            logger.addHandler(stream_handler)

        if logfile:
            logfile = os.path.abspath(logfile)
            file_handler = logging.FileHandler(logfile)
            file_handler.setFormatter(log_format)
            logger.addHandler(file_handler)

    return logger
