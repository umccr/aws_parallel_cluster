#!/usr/bin/env python3

"""
Check functions
"""

from umccr_utils.logger import get_logger
from umccr_utils.errors import NoCondaEnvError, PClusterVersionFailure, AWSVersionFailureError, AWSCredentialsError
from umccr_utils.aws_wrappers import get_aws_version, check_credentials
from umccr_utils.miscell import get_conda_env, get_pcluster_version
from packaging import version

logger = get_logger()


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
    if not get_conda_env() == "pcluster":
        raise NoCondaEnvError

    if get_pcluster_version() is None:
        raise PClusterVersionFailure

    if not version.parse(get_aws_version()) >= version.parse("2.0.0"):
        raise AWSVersionFailureError

    try:
        check_credentials()
    except AWSCredentialsError:
        raise AWSCredentialsError
