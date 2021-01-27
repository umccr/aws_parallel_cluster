#!/usr/bin/env python3

"""
Random functions that don't quite go anywhere
"""

import subprocess
import os
import getpass
from umccr_utils.logger import get_logger
from umccr_utils.errors import NoCondaEnvError
import json

logger = get_logger()


def get_conda_prefix():
    """
    Return the path of the conda prefix environment
    :return:
    """
    conda_prefix = os.environ.get("CONDA_PREFIX")

    if conda_prefix is None:
        raise NoCondaEnvError

    return conda_prefix


def get_conda_env():
    """
    Check we're in the pcluster environment.
    :return:
    """
    conda_env = os.environ.get("CONDA_DEFAULT_ENV")

    if conda_env is None:
        raise NoCondaEnvError

    return conda_env


def get_pcluster_version():
    """
    Return the version of parallel cluster
    :return:
    """

    pcluster_version_command = ["pcluster", "version"]

    pcluster_version_returncode, pcluster_version_output, pcluster_version_error = \
        run_subprocess_proc(pcluster_version_command, capture_output=True)

    return pcluster_version_output


def get_user():
    """
    Return the user name
    :return:
    """
    return getpass.getuser()


def run_subprocess_proc(*args, **kwargs):
    """
    Utilities runner for running a subprocess command and printing log files
    :param args:
    :param kwargs:
    :return:
    """

    subprocess_proc = subprocess.run(*args, **kwargs)

    command_str = '" "'.join(subprocess_proc.args) \
        if type(subprocess_proc.args) == list \
        else subprocess_proc.args
    command_str = '"' + command_str + '"'

    # Get outputs
    if subprocess_proc.stdout is not None:
        command_stdout = subprocess_proc.stdout.decode()
    else:
        command_stdout = None

    if subprocess_proc.stderr is not None:
        command_stderr = subprocess_proc.stderr.decode()
    else:
        command_stderr = None

    # Get return code
    command_returncode = subprocess_proc.returncode

    if not command_returncode == 0:
        # Print returncode to warning
        logger.warning("Received exit code \"{}\" for command {}".format(
            command_returncode,
            command_str
        ))
        # Print stdout/stderr to console
        logger.warning("Stdout was: \n\"{}\"".format(command_stdout.strip()))
        logger.warning("Stderr was: \n\"{}\"".format(command_stderr.strip()))
    else:
        # Let debug know command returned successfully
        logger.debug("Command \"{}\" returned successfully".format(command_str))
        # Print stdout/stderr to console
        logger.debug("Stdout was: \n\"{}\"".format(command_stdout.strip()))
        logger.debug("Stderr was: \n\"{}\"".format(command_stderr.strip()))

    return command_returncode, command_stdout, command_stderr


def json_to_str(json_obj):
    """

    :return:
    """

    return json.dumps(json_obj)
