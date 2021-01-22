#!/usr/bin/env python3

def get_ssm_login_help():
    """
    Print the assistance on setting up the ssh config s.t one can run the ssm command to log into the node
    :return:
    """
    ssm_help_str = """
    ssm is a bash function defined as so
    
    ssm() {
      : '
      ssh into the ec2 instance.
      params: instance_id - should start with 'i-'
      '
      local instance_id
      instance_id="$1"
      aws ssm start-session \
        --target "${instance_id}" \
        --document-name AWS-StartInteractiveCommand \
        --parameters command="sudo su - ec2-user"
    }
    
    With the one positional parameter being the ec2-instance id you would like to log in to.  
    Using this command means that no ssh key is needed in order to connect to the node, nor is port 22 required 
    to be open on the instance in order to connect.
    """

    return ssm_help_str


def get_parallel_cluster_extended_help():
    """
    Returns a list of help for running aws parallel cluster
    :return:
    """

    getting_started_help = """
    Welcome to UMCCR's AWS Parallel cluster. There are three main functions you need to worry about.
    
    ## Starting a cluster
    Getting started with a cluster is super simple - just call the command like so:
    start_cluster.py --cluster-name <NAME_OF_YOUR_CLUSTER>
    
    We also cater for the option of multiple filesystem types and adding in extra tags to each cluster.
    
    ## Logging into a cluster
    
    Shown below is the bash alias required to make sure you can easily login with aws' ssm start-session command. 
    Make sure you have aws v2 installed on your PATH variable and the ssm alias as shown below.  
    
    {}
    
    You may now log into your cluster with ssm <parallel-cluster-master-instance-id>
    
    ## Listing Clusters
    
    This command requires no parameters:
    
    list_clusters.py
    
    Will return the cluster name, master node instance id, along with the user that created the cluster.  
    
    ## Stopping a cluster
    
    This will shut down a cluster 
    
    stop_cluster.py --cluster-name <NAME_OF_CLUSTER_TO_CLOSE>
    
    """.format(get_ssm_login_help())

    return getting_started_help


def print_extended_help():
    """
    Print the extended help to the console
    :return:
    """

    print(get_parallel_cluster_extended_help())

