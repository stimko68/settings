"""
Common module used for shell functions
"""
import logging
import os
import shlex
import subprocess


def run_shell_command(cmd, full_output=False, command_directory=os.getcwd(), log_domain='', realtime_output=True,
                      **flags):
    """Run a shell command and return the status code.

    Given a command run it and return the status code. This function can
    return the output of the command as well if `full_output=True`.

    :param cmd:                 Shell command to execute. Can be a string or a list.
    :type cmd:                  str or list
    :param full_output:         Flag to determine whether or not to return
                                the output of the shell command.
    :type full_output:          bool
    :param command_directory:   Directory from which to execute the command. Default
                                is the current working directory.
    :type command_directory:    str
    :param log_domain:          Specify a log domain to send logging output to.
    :type log_domain:           str
    :param realtime_output      Specify whether to immediately tail the output of the command
    :type realtime_output       bool
    :param flags:               Additional options that should be passed to `Popen` can be
                                given as kwargs.
    :type flags:                kwargs
    :return:                    Return code from the executed command. If `full_output=True`
                                then the output from the command is returned as well.
    :rtype:                     int or tuple(int, list)
    """
    output = list()

    log = logging.getLogger(log_domain)
    log.info(f'Running command: {cmd}')

    subprocess_flags = {
        'close_fds': True,
        'cwd': command_directory,
        'stderr': subprocess.STDOUT,
        'stdout': subprocess.PIPE,
    }

    subprocess_flags.update(flags)

    # Check if the 'input' flag was passed. If so then make sure the value is a byte string
    input_value = subprocess_flags.get('input')
    if input_value:
        try:
            subprocess_flags['input'] = input_value.encode()
        except AttributeError:
            pass

    if type(cmd) == str:
        cmd = shlex.split(cmd)

    process = subprocess.Popen(cmd, **subprocess_flags)

    for line in iter(process.stdout.readline, b''):
        if realtime_output:
            log.info(line.strip().decode())
        output.append(line.decode())

    process.stdout.close()
    return_code = process.wait()

    if full_output:
        return return_code, output
    else:
        return return_code
