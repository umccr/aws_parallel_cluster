#!/usr/bin/env python3

"""
All possible things that could go wrong
"""


class AWSCredentialsError(Exception):
    """
    No AWS Credentials found
    """
    pass


class NoCondaEnvError(Exception):
    """
    We're not in a conda env
    """
    pass


class NoLocalIPError(Exception):
    """
    Could not retrieve a local ip
    """
    pass


class AWSBinaryNotFoundError(Exception):
    """
    Could not find the AWS Binary
    """
    pass


class AWSVersionFailureError(Exception):
    """
    Could not get a valid AWS version (>2)
    """
    pass


class PClusterBinaryNotFoundError(Exception):
    """
    Could not get the pcluster binary
    """
    pass


class PClusterCreateError(Exception):
    """
    Could not create the parallel cluster conda environment
    """
    pass


class PClusterVersionFailure(Exception):
    """
    Got the incorrect version of parallel cluster
    """
    pass


class PClusterInstanceError(Exception):
    """
    Got the pcluster instance error
    """
    pass


class AMINotFoundError(Exception):
    """
    Could not find the ami based on the tags created
    """
    pass


class SSMParameterError(Exception):
    """
    Couldn't evaluate the value of the ssm parameter correctly
    """
    pass