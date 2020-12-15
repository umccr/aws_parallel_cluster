#!/usr/bin/env python3

"""
List available clusters
"""

import pandas as pd
from umccr_utils.aws_wrappers import check_credentials, get_master_ec2_instance_id_from_pcluster_id
from umccr_utils.miscell import run_subprocess_proc
from umccr_utils.logger import get_logger
from umccr_utils.globals import AWS_REGION
from umccr_utils.help import print_extended_help
from io import StringIO
import boto3


logger = get_logger()


def get_args():
    """
    Whilst there's no reason for us to have this,
    maybe in future we ought to specify the region used
    :return:
    """

    parser = argparse.ArgumentParser(description="List the currently running clusters")

    parser.add_argument("--help-ext",
                        description="Print the extended help",
                        required=False)

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

    cluster_list_returncode, cluster_list_stdout, cluster_list_stderr = run_subprocess_proc(cluster_list_command)

    cluster_columns = ["Name", "Status", "Version"]

    clusters_as_df = pd.DataFrame([[row.split(" ")]
                                   for row in cluster_list_stdout.split("\n")],
                                  columns=cluster_columns)

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
    output = StringIO()

    cluster_df.to_csv(output, index=False, header=True)


def main():
    args = get_args()

    if getattr(args, "help_ext", None) is not None:
        print_extended_help()

    cluster_df = get_cluster_list()

    cluster_df["Master"] = cluster_df["Name"].apply(get_master_ec2_instance_id_from_pcluster_id)

    cluster_df["Creator"] = cluster_df["Master"].apply(get_creator_tag)

    print_df(cluster_df)


if __name__ == "__main__":
    main()
