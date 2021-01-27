#!/usr/bin/env python3

"""
AWS commands to run and validate outputs from
"""

import boto3
from botocore.exceptions import UnauthorizedSSOTokenError
from umccr_utils.miscell import run_subprocess_proc, get_user
from umccr_utils.logger import get_logger
from packaging import version
from umccr_utils.errors import NoLocalIPError, AWSCredentialsError, AWSBinaryNotFoundError, AWSVersionFailureError, \
    PClusterBinaryNotFoundError, PClusterVersionFailure, PClusterInstanceError, AMINotFoundError, SSMParameterError
from umccr_utils.globals import AWS_REGION, AWS_ACCOUNT_MAPPING, AWS_PARALLEL_CLUSTER_STACK_NAME
from datetime import datetime
import shlex

logger = get_logger()

CREATION_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def get_aws_account_name():
    client = boto3.client("sts")

    try:
        caller_id = client.get_caller_identity()
    except UnauthorizedSSOTokenError:
        raise AWSCredentialsError

    account = caller_id['Account']

    if account not in AWS_ACCOUNT_MAPPING.keys():
        raise AWSCredentialsError

    return AWS_ACCOUNT_MAPPING[account]


def get_parallel_cluster_ami_stack_name():
    """
    Returns AWS_PARALLEL_CLUSTER_STACK_NAME global
    Must be identical to the stack tag given in the cdk ami
    :return:
    """

    return AWS_PARALLEL_CLUSTER_STACK_NAME


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
        logger.error("Could not find user id after calling 'get_caller_identity' function."
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
    aws_type_return, aws_type_stdout, aws_type_stderr = run_subprocess_proc(["bash", "-c", shlex.join(aws_type_command)],
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
    if 'aws-cli' not in [command[0] for command in command_version_split]:
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


def get_parallel_cluster_s3_path(s3_path_ssm_parameter_key):
    """
    Get the base path for the parallel cluster s3 location
    :return:
    """

    s3_path_ssm_parameter_value = ssm_parameter_value(s3_path_ssm_parameter_key,
                                                      encrypted=False)

    return s3_path_ssm_parameter_value


def get_ami_id(version):
    """
    Get the ami id for this version of aws parallel cluster
    Uses a tag based approach to find the correct ami for this parallel cluster version
    :param version:
    :return:
    """

    ec2 = boto3.client("ec2")

    images_dict = ec2.describe_images(
            Filters=[
                {
                    "Name": "tag:Stack",
                    "Values": [
                        get_parallel_cluster_ami_stack_name()
                    ]
                },
                {
                    "Name": "tag:Version",
                    "Values": [
                        version
                    ]
                }
            ],
            Owners=["self"]
        )

    # Check if there's only one image (which there should be)
    if len(images_dict["Images"]) == 0:
        logger.error("Could not retrieve the image id")
        logger.error("No image with the the stack tag '{}' and version tags '{}' could be found for this aws user".format(
            get_parallel_cluster_ami_stack_name(), version
        ))
        raise AMINotFoundError
    elif len(images_dict["Images"]) == 1:
        return images_dict["Images"][0]["ImageId"]
    else:
        # Get the latest created image
        latest_creation = None
        for image in images_dict["Images"]:
            if latest_creation is None or \
                datetime.strptime(image["CreationDate"], CREATION_TIME_FORMAT) > \
                    datetime.strptime(latest_creation["CreationDate"], CREATION_TIME_FORMAT):
                latest_creation = image
        return latest_creation["ImageId"]


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

    if "Parameter" not in parameter.keys():
        logger.error("SSM parameter \"{}\" doesn't exist".format(ssm_parameter_name))
        raise SSMParameterError

    if "Value" not in parameter["Parameter"].keys():
        logger.error("SSM parameter \"{}\" doesn't have 'Value' attribute. "
                     "Check encryption value has been parsed correctly".format(ssm_parameter_name))
        raise SSMParameterError

    return parameter["Parameter"]["Value"]

