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
from umccr_utils.globals import AWS_REGION
from umccr_utils.help import print_extended_help
from umccr_utils.checks import check_env
from io import StringIO
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

    if cluster_list_stdout is not None:
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

    return ec2instance.tags["Creator"]


def print_df(cluster_df):
    """
    Print the dataframe of available clusters
    :return:
    """
    import sys

    cluster_df.to_csv(sys.stdout, index=False, header=True)


def main():
    # Get args
    args = get_args()

    if getattr(args, "help_ext", False):
        print_extended_help()

    # Check the environment
    check_env()

    # Get the cluster df
    cluster_df = get_cluster_list()

    # Add Master column
    cluster_df["Master"] = cluster_df.apply(lambda x: np.nan if x.Status in ["CREATE_IN_PROGRESS"] else get_master_ec2_instance_id_from_pcluster_id(x.Name),
                                            axis="columns")

    # Add Creator column
    cluster_df["Creator"] = cluster_df.apply(lambda x: get_creator_tag(x.Master) if not pd.isna(x.Master) else np.nan,
                                             axis="columns")

    print_df(cluster_df)


if __name__ == "__main__":
    main()
