#!/usr/bin/env python3

"""
Start a cluster
"""

import argparse
import json
from json.decoder import JSONDecodeError
from umccr_utils.logger import get_logger
from umccr_utils.aws_wrappers import get_master_ec2_instance_id_from_pcluster_id, get_aws_account_name
import tempfile
from umccr_utils.miscell import json_to_str, run_subprocess_proc, check_env
from umccr_utils.help import print_extended_help
from umccr_utils.errors import PClusterCreateError
import configparser
from umccr_utils.globals import \
    AWS_GLOBAL_SETTINGS, AWS_REGION, AWS_CLUSTER_BASICS, AWS_NETWORK, \
    AWS_PARTITION_QUEUES, AWS_FILESYSTEM, AWS_COMPUTE_RESOURCES, AWS_ALIASES
import sys

logger = get_logger()


def get_args():
    """
    Get arguments from CLI
    :return:
    """

    parser = argparse.ArgumentParser(description="Start up a parallel cluster")

    parser.add_argument("--cluster-name",
                        help="Name of the cluster you would like to launch",
                        required=True)

    parser.add_argument("--file-system-type",
                        help="The type of file system to use for the cluster",
                        choices=["efs", "fsx"],
                        default="efs")

    parser.add_argument("--no-rollback",
                        help="Do you wish to add the --norollback option to the pcluster create command",
                        action="store_true",
                        default=False)

    parser.add_argument("--extra-parameters",
                        help="json as str key-pair values to add to the extra-parameters options",
                        required=False)

    parser.add_argument("--tags",
                        help="json-as-str key-pair values for tags to be used.",
                        required=False)

    parser.add_argument("--help-ext",
                        help="Print extended help",
                        required=False)

    args = parser.parse_args()

    return args


def set_args(args):
    """
    Set / Check arguments retrieved
    :return:
    """

    # Check extra-parameters can be loaded as a json string
    extra_parameters_arg = getattr(args, "extra-parameters", None)

    if extra_parameters_arg is not None:
        extra_parameters_json = str_to_json(extra_parameters_arg)
        setattr(args, "extra-parameters-json", extra_parameters_json)
    else:
        setattr(args, "extra-parameters-json", None)

    # Check tag parameters can be loaded as a json string
    tag_parameters_arg = getattr(args, "tags", None)

    if tag_parameters_arg is not None:
        tag_parameters_json = str_to_json(tag_parameters_arg)
        setattr(args, "tag-parameters-json", tag_parameters_json)
    else:
        setattr(args, "tag-parameters-json", None)

    return args


def str_to_json(json_str):
    try:
        logger.info("")
        json_obj = json.loads(json_str)
    except JSONDecodeError:
        logger.error("Could not read \"{}\" as a json".format(json_str))
        raise JSONDecodeError

    return json_obj


def collate_pcluster_create_cli(cluster_name, configuration_file, extra_parameters=None, tags=None, no_rollback=False):
    """
    Import options to create the pcluster create command
    :return:
    """
    pcluster_create_command = ["pcluster", "create",
                               "--config", configuration_file]

    if extra_parameters is not None:
        pcluster_create_command.extend(["--extra-parameters", json_to_str(extra_parameters)])

    if tags is not None:
        pcluster_create_command.extend(["--tags", json_to_str(tags)])

    if no_rollback:
        pcluster_create_command.append("--norollback")

    pcluster_create_command.append(cluster_name)

    return pcluster_create_command


def create_configuration_file(args):
    """
    Given the arguments, on the cli, create the config required for the cluster to be built

    Configuration requires the following components
    * aws
    * global
    * cluster <cluster-name>
    * vpc <network-name>
    * <filesystem-type> <filesystem-name>
    * queue <queue-name> (can be specified multiple times)
    * compute_resource <resource-name> (can be specified multiple times)
    * aliases (optional)
    :return:
    """

    configuration_temp_file = tempfile.NamedTemporaryFile()

    pcluster_config = configparser.ConfigParser()

    # Add aws and globals settings
    pcluster_config["aws"] = {"region": AWS_REGION}
    pcluster_config["globals"] = AWS_GLOBAL_SETTINGS

    # Intialise cluster
    pcluster_config["cluster {}".format(args.cluster_name)] = AWS_CLUSTER_BASICS

    # Add in network settings:
    pcluster_config["vpc {}_network".format(args.cluster_name)] = AWS_NETWORK[get_aws_account_name()]
    pcluster_config["cluster {}".format(args.cluster_name)]["vpc_settings"] = "{}_network".format(args.cluster_name)

    # Add in file system settings
    pcluster_config["{} {}_fs".format(args.file_system_type, args.cluster_name)] = \
        AWS_FILESYSTEM[args.file_system_type]
    pcluster_config["cluster {}".format(args.cluster_name)]["{}_settings".format(args.file_system_type)] = \
        "{}_fs".format(args.cluster_name)

    # Add queue settings to cluster config for each queue
    for queue_name, queue_dict in AWS_PARTITION_QUEUES.items():
        pcluster_config["queue {}".format(queue_name)] = queue_dict
    pcluster_config["cluster {}".format(args.cluster_name)]["queue_settings"] = \
        ", ".join(list(AWS_PARTITION_QUEUES.keys()))

    # Add compute resoures to cluster config
    for queue_name, queue_dict in AWS_PARTITION_QUEUES.items():
        compute_type = queue_dict["compute_type"]
        for compute_resource in queue_dict["compute_resource_settings"]:
            pcluster_config["compute_resource {}_{}".format(compute_resource, compute_type)] = \
                AWS_COMPUTE_RESOURCES[compute_resource]

    # Add aliases to cluster config
    pcluster_config["aliases"] = AWS_ALIASES

    return configuration_temp_file


def run_pcluster_create(pcluster_create_command):
    """
    Run pcluster create command
    :return:
    """
    pcluster_create_returncode, pcluster_create_stdout, pcluster_create_stderr = \
        run_subprocess_proc(pcluster_create_command)

    if not pcluster_create_returncode == 0:
        logger.error("Failed to create the stack successfully")

        raise PClusterCreateError


def log_success_message(ec2_instance):
    """
    Show user how to log into the compute node via ssm to stderr
    :return:
    """

    login_message = """
    
    You can now log in to your master node of your parallel cluster instance by using the following command:
    
    ssm "{}"
    
    Where "ssm" is an alias. Please use --help-ext to show the full alias you will need.
    
    """.format(ec2_instance)

    return login_message


def main():
    """
    get args
    set args
    check env
    Generate config
    Run 'create pcluster'
    Log success message
    """

    args = get_args()

    if getattr(args, "help_ext", None) is not None:
        print_extended_help()
        sys.exit(0)

    args = set_args(args)

    # Check environment vars
    check_env()

    configuration_file = create_configuration_file(args)

    pcluster_create_command = collate_pcluster_create_cli(cluster_name=args.cluster_name,
                                                          configuration_file=configuration_file,
                                                          extra_parameters=args.extra_parameters_json,
                                                          tags=args.tags_json,
                                                          no_rollback=args.no_rollback)

    run_pcluster_create(pcluster_create_command)

    master_node = get_master_ec2_instance_id_from_pcluster_id(args.cluster_name)

    log_success_message(ec2_instance=master_node)


if __name__ == "__main__":
    main()
