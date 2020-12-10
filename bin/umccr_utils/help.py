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
