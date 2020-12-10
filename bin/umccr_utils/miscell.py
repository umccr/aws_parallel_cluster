#!/usr/bin/env python3

"""
Random functions that don't quite go anywhere
"""

import subprocess
import os
from pathlib import Path
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
    return os.environ["CONDA_PREFIX"]


def get_conda_env():
    """
    Check we're in the pcluster environment.
    :return:
    """
    conda_env = os.environ["CONDA_DEFAULT_ENV"]

    if conda_env is None:
        raise NoCondaEnvError

    return conda_env


def check_env():
    """
    Check we're in the right environment
    * Right pcluster conda env?
    * Right pcluster version?
    * Latest pcluster version?
    * Right aws version?
    * Logged in to AWS?
    * We have an IP address?
    :return:
    """
    # TODO


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

    subprocess_proc = subprocess.run(*args, *kwargs)

    command_str = "'".join(subprocess_proc.args) \
        if type(subprocess_proc.args) == list \
        else subprocess_proc.args

    # Get outputs
    command_stdout = subprocess_proc.stdout.decode()
    command_stderr = subprocess_proc.stderr.decode()

    # Get return code
    command_returncode = subprocess_proc.returncode

    if command_returncode == 0:
        # Print returncode to warning
        logger.warning("Received exit code \"{}\" for command {}".format(
            command_returncode,
            command_str
        ))
        # Print stdout/stderr to console
        logger.warning("Stdout was: \"{}\"".format(command_stdout))
        logger.warning("Stderr was: \"{}\"".format(command_stderr))
    else:
        # Let debug know command returned successfully
        logger.debug("Command \"{}\" returned successfully".format(command_str))
        # Print stdout/stderr to console
        logger.debug("Stdout was: \"{}\"".format(command_stdout))
        logger.debug("Stderr was: \"{}\"".format(command_stderr))

    return command_returncode, command_stderr, command_stderr


def json_to_str(json_obj):
    """

    :return:
    """

    return json.dumps(json_obj)


