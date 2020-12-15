#!/usr/bin/env python3

"""
Global params - mostly used to generate the configuration file
"""

AWS_REGION = "ap-southeast-2"

UOM_IP_RANGE = ""  # TODO

AWS_NETWORK = {
    "tothill": {
        "network": {
          "vpc_id": "vpc-06daaa8ca8e5c853e",
          "master_subnet_id": "subnet-061d824f3056967b5",
          "use_public_ips": "true",
          "additional_sg": "sg-0b4296d2fae709454"
        }
    },
    "umccr_dev": {
        "network": {
          "vpc_id": "vpc-00eafc63c0dfca266",
          "master_subnet_id": "subnet-0fab038b0341872f1",
          "use_public_ips": "true",
          "additional_sg": "sg-0ca5bdaab39885649"
        }
    },
}

AWS_FILESYSTEM = {
    "efs": {
      "shared_dir": "efs",
      "encrypted": "true",
      "performance_mode": "generalPurpose"
    },
    "fsx": {
      "shared_dir": "/fsx",
      "storage_capacity": 1200,
      "deployment_type": "SCRATCH_2"
    }
}

AWS_PARTITION_QUEUES = {
    "compute": {
       "compute_resource_settings": [
           "hi_cpu", "hi_mem"
       ],
       "compute_type": "spot"
    },
    "compute-long": {
       "compute_resource_settings": [
           "hi_cpu", "hi_mem"
       ],
       "compute_type": "ondemand"
    },
    "copy": {
        "compute_resource_settings": [
            "hi_network"
        ],
        "compute_type": "spot"
    },
    "copy-long": {
        "compute_resource_settings": [
            "hi_network"
        ],
        "compute_type": "ondemand"
    }
}

AWS_COMPUTE_RESOURCES = {
    "hi_cpu": {
        "instance_type": "c5.4xlarge"
    },
    "hi_mem": {
        "instance_type": "m5.4xlarge"
    },
    "hi_network": {
        "instance_type": "m5.large"
    }
}

AWS_GLOBAL_SETTINGS = {
    "update_check": "true",
    "santity_check": "true"
}

AWS_CLUSTER_BASICS = {
    "base_os": "alinux2",
    "master_instance_type": "t2.medium",
    "key_name": "pc-default-key",
    "s3_read_resource": "*",
    "additional_iam_policies": "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
    "scheduler": "slurm",
    # FIXME update __VERSION__ in 'pre_install' and 'post_install' globals? - could be done install.sh side?
    "pre_install": "s3://tothill-parallel-cluster-dev/__VERSION__/bootstrap/pre_install.sh",
    "post_install": "s3://tothill-parallel-cluster-dev/__VERSION__/bootstrap/post_install.sh",
    "custom_ami": "ami-074416eece29e32ec",  # FIXME - this should be retrieved from somewhere, like an ssm parameter
    "master_root_volume_size": "45",
    "compute_root_volume_size": "60"
}

AWS_ALIASES = {
    "ssh": "ssh {CFN_USER}@{MASTER_IP} {ARGS}"
}

AWS_ACCOUNT_MAPPING = {
    "umccr_dev": "843407916570",
    "tothill": "206808631540"
}