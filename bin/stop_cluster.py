#!/usr/bin/env python3

"""
Delete/Stop a cluster
"""

import sys
import argparse
from umccr_utils import logger
from umccr_utils.help import print_extended_help
from umccr_utils.checks import check_env
from umccr_utils.miscell import run_subprocess_proc
from umccr_utils.globals import AWS_REGION
logger = logger.get_logger()


def get_args():
    """
    Cluster name
    :return:
    """

    parser = argparse.ArgumentParser(description="Stop the cluster")

    parser.add_argument("--cluster-name",
                        help="Name of the cluster to shut down",
                        required=True)

    parser.add_argument("--help-ext",
                        help="Print the extended help",
                        action="store_true",
                        required=False)

    args = parser.parse_args()

    return args


def stop_cluster(cluster_name):
    """
    Read in cluster list as pandas dataframe
    :return:
    """

    stop_cluster_command = ["pcluster", "delete",
                            "--region", AWS_REGION,
                            cluster_name]

    cluster_list_returncode, cluster_list_stdout, cluster_list_stderr = run_subprocess_proc(stop_cluster_command,
                                                                                            capture_output=True)

    if not cluster_list_returncode == 0:
        logger.error("Could not successfully delete the cluster, exiting")
        sys.exit(1)

    return cluster_list_stdout


def main():

    if "--help-ext" in sys.argv:
        print_extended_help()
        sys.exit(0)

    args = get_args()

    # Check we're logged in
    check_env()

    # Stop the cluster
    stop_cluster(args.cluster_name)


if __name__ == "__main__":
    main()
