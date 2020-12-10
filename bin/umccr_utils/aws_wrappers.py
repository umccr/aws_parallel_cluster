#!/usr/bin/env python3

"""
AWS commands to run and validate outputs from
"""

import boto3
from botocore.exceptions import UnauthorizedSSOTokenError
from miscell import run_subprocess_proc, get_user
from logger import get_logger
from packaging import version
from umccr_utils.errors import NoLocalIPError, AWSCredentialsError, AWSBinaryNotFoundError, AWSVersionFailureError, PClusterBinaryNotFoundError, PClusterVersionFailure, PClusterInstanceError
from umccr_utils.globals import AWS_REGION, AWS_ACCOUNT_MAPPING

logger = get_logger()


def get_aws_account_name():
    client = boto3.client("sts")

    try:
        caller_id = client.get_caller_identity()
    except UnauthorizedSSOTokenError:
        raise AWSCredentialsError

    # TODO put this through a try-except
    return AWS_ACCOUNT_MAPPING[caller_id['Account']]


def check_credentials():
    """
    Ensure user has AWS credentials
    :return:
    """

    client = boto3.client("sts")

    try:
        caller_id = client.get_caller_identity()
    except UnauthorizedSSOTokenError:
        raise AWSCredentialsError

    if not ['UserId'] in caller_id.keys():
        logger.error("Could not find user id after calling 'get_caller_identity_function'."
                     "Got the following keys instead: \"{}\"".format(", ".join(caller_id.keys())))
        raise AWSCredentialsError


def get_aws_version():
    """
    Get the version of aws that the user is got
    :return:
    """

    # type is a universal command, should return a zero-exit code if aws is an alias/binary etc in the user's path
    aws_type_command = ["type", "-p", "aws"]  # Should return /usr/local/bin/aws

    # Run through subprocess wrapper
    aws_type_return, aws_type_stdout, aws_type_stderr = run_subprocess_proc(aws_type_command,
                                                                            capture_output=True)

    if not aws_type_return == 0:
        raise AWSBinaryNotFoundError

    aws_version_command = ["aws", "--version"]

    # Run through subprocess wrapper
    aws_version_return, aws_version_stdout, aws_version_stderr = run_subprocess_proc(aws_version_command,
                                                                                     capture_output=True)

    if not aws_version_return == 0:
        raise AWSVersionFailureError

    command_version_split = [tuple(command_version.split("/", 1))
                             for command_version in aws_version_stdout.split(" ")]

    # Check aws-cli is in commands
    if 'aws-cli' not in [command for command in command_version_split]:
        logger.error("Could not find aws-cli version in \"{}\"".format(aws_version_stdout))
        raise AWSVersionFailureError

    aws_cli_version = [version
                       for command, version in command_version_split
                       if command == "aws-cli"][0]

    return aws_cli_version


def is_aws_v2():
    """
    Ensure the aws binary is a version 2 binary

    :return:
    """
    aws_version = get_aws_version()

    if not version.parse(aws_version) > version.parse("2"):
        logger.error("AWS version must be higher than 2, got \"{}\"".format(aws_version))
        raise AWSVersionFailureError


def get_pcluster_version():
    """
    Check pcluster version is appropriate
    :return:
    """
    # type is a universal command, should return a zero-exit code if aws is an alias/binary etc in the user's path
    pcluster_type_command = ["type", "-p", "pcluster"]  # Should return "${CONDA_PREFIX}/bin/pcluster"

    # Run through subprocess wrapper
    pcluster_type_return, pcluster_type_stdout, pcluster_type_stderr = run_subprocess_proc(
        pcluster_type_command, capture_output=True)

    if not pcluster_type_return == 0:
        raise PClusterBinaryNotFoundError

    pcluster_version_command = ["pcluster", "version"]

    # Run through subprocess wrapper
    pcluster_version_return, pcluster_version_stdout, pcluster_version_stderr = \
        run_subprocess_proc(pcluster_version_command, capture_output=True)

    # Raise version failure if we couldn't get a result
    if not pcluster_version_return == 0:
        raise PClusterVersionFailure

    return pcluster_type_stdout


def get_master_ec2_instance_id_from_pcluster_id(pcluster_id):
    """
    Use some jq magic to get the master ec2 instance id from a pcluster id
    :return:
    """

    # Use the pcluster instances command to retrieve information about a stack
    pcluster_instances_command = ["pcluster", "instances",
                                  "--region", AWS_REGION,
                                  pcluster_id]

    # Get returncode, stdout, stderr
    pcluster_instances_returncode, pcluster_stdout, pcluster_stderr = run_subprocess_proc(pcluster_instances_command)

    if not pcluster_instances_returncode == 0:
        raise PClusterInstanceError

    # Get the Master Server
    for instance_row in pcluster_stdout.split("\n"):
        if instance_row.startswith("MasterServer"):
            return instance_row.rsplit(" ", 1)[-1]

    logger.error("Could not find Master server after running command \"{}\"".
                 format(' '.join(pcluster_instances_command)))
    raise PClusterInstanceError


def get_local_ip():
    """
    Get the local ip address of the user - ideally two 'accessForms' are created
    One for the user's IP and one for UOM in case they're using a VPN.
    :return:
    """

    get_local_ip_command = ["dig", "+short", "myip.opendns.com", "@resolver1.opendns.com"]

    get_local_ip_return, get_local_ip_stdout, get_local_ip_stderr = run_subprocess_proc(
        get_local_ip_command, capture_output=True)

    if not get_local_ip_return == 0:
        logger.error("Could not get local ip")
        raise NoLocalIPError

    return get_local_ip_stdout


def get_parallel_cluster_tags(tags):
    """
    Get the tags for the parallel cluster command
    Will return a 'Creator' tag,
    And should also have a UseCase tag
    And should also have a 'Name' tag
    and a 'Stack' tag set to ParallelCluster
    :return:
    """

    # Make sure we don't override input dict
    tags = tags.copy()

    # Get a user tag
    if "Creator" not in tags.keys():
        tags["Creator"] = get_user()

    # Get a UseCase tag
    if "UseCase" not in tags.keys():
        tags["UseCase"] = "ParallelCluster"

    # Get a Name tag
    if "Name" not in tags.keys():
        tags["Name"] = "ParallelCluster"

    # Get a Stack tag
    if "Stack" not in tags.keys():
        tags["Stack"] = "ParallelCluster"

    return tags


def ssm_parameter_value(ssm_parameter_name, encrypted=False):
    """
    Return the value from ssm parameter store
    :return:
    """

    ssm = boto3.client("ssm")

    parameter = ssm.get_parameter(Name=ssm_parameter_name,
                                  WithDecryption=encrypted)

    return parameter
