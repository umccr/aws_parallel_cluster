#!/usr/bin/env python3

"""
List available clusters
"""

import pandas as pd
import numpy as np
import argparse
from umccr_utils.aws_wrappers import check_credentials, get_master_ec2_instance_id_from_pcluster_id
from umccr_utils.miscell import run_subprocess_proc
from umccr_utils.logger import get_logger
from umccr_utils.globals import AWS_REGION, CFN_STATUSES
from umccr_utils.help import print_extended_help
from umccr_utils.checks import check_env
import boto3
import sys


logger = get_logger()


def get_args():
    """
    Whilst there's no reason for us to have this,
    maybe in future we ought to specify the region used
    :return:
    """

    parser = argparse.ArgumentParser(description="List the currently running clusters")

    parser.add_argument("--help-ext",
                        help="Print the extended help",
                        action="store_true",
                        required=False)

    args = parser.parse_args()

    return args


def complete_checks():
    """
    Run through checklist
    :return:
    """

    check_credentials()


def get_cluster_list():
    """
    Read in cluster list as pandas dataframe
    :return:
    """

    cluster_list_command = ["pcluster", "list",
                            "--region", AWS_REGION]

    cluster_list_returncode, cluster_list_stdout, cluster_list_stderr = run_subprocess_proc(cluster_list_command,
                                                                                            capture_output=True)

    cluster_columns = ["Name", "Status", "Version"]

    if cluster_list_stdout is not None and not cluster_list_stdout.strip() == "":
        clusters_as_df = pd.DataFrame([row.split()
                                       for row in cluster_list_stdout.strip().split("\n")],
                                      columns=cluster_columns)
    else:
        logger.info("No clusters found")
        sys.exit(0)

    return clusters_as_df


def get_creator_tag(master_id):
    """
    Retrieve the Creator tag from the master instance id tags
    :return:
    """
    resource = boto3.resource("ec2")

    ec2instance = resource.Instance(master_id)

    # Check "tags" is an attribute of the instance.
    if getattr(ec2instance, "tags", None) is None:
        return None

    # Iterate through the list of tags
    for tag in ec2instance.tags:
        if tag["Key"] == "Creator":
            return tag["Value"]
    # Found nothing, return
    return None


def print_df(cluster_df):
    """
    Print the dataframe of available clusters
    :return:
    """
    import sys

    cluster_df.to_string(sys.stdout, index=False, header=True)
    # Print an empty line to finish
    print()


def get_headnode_from_pcluster_row(pd_series):
    """
    From the cluster list collect the id of the head node, given the pcluster has completed
    :param pd_series:
    :return:
    """

    if pd_series['Status'] in CFN_STATUSES["completed"]:
        return get_master_ec2_instance_id_from_pcluster_id(pd_series["Name"])

    return np.nan


def get_creator_from_head_node_tag(pd_series):
    """
    From the cluster list collect the id of the head node, given the pcluster has completed
    :param pd_series:
    :return:
    """

    # Check head node exists Head node
    if not pd.isna(pd_series["Head Node"]):
        creator = get_creator_tag(pd_series["Head Node"])
    else:
        # Return NA if no head node
        return np.nan

    # Check creator also isn't none
    if creator is not None:
        return creator

    return np.nan


def main():

    # Print extended help
    if "--help-ext" in sys.argv:
        print_extended_help()
        sys.exit(0)

    # Get args
    _ = get_args()

    # Check the environment
    check_env()

    # Get the cluster df
    cluster_df = get_cluster_list()

    # Add Master column
    cluster_df["Head Node"] = cluster_df.apply(get_headnode_from_pcluster_row,
                                                axis="columns")

    # Add Creator column
    cluster_df["Creator"] = cluster_df.apply(get_creator_from_head_node_tag,
                                             axis="columns")

    print_df(cluster_df)


if __name__ == "__main__":
    main()
