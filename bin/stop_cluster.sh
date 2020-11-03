#!/bin/bash

###########
# FUNCTIONS
###########

echo_stderr(){
    # Write log to stderr
    echo "${@}" 1>&2
}

has_creds(){
  : '
  Are credentials present on CLI
  '
  aws sts get-caller-identity >/dev/null 2>&1
  return "$?"
}

# Check version
check_pcluster_version() {
  # Used to ensure that pcluster is in our PATH
  pcluster version >/dev/null 2>&1
  return "$?"
}

display_help() {
    echo "Usage: $0 NAME_OF_YOUR_CLUSTER" >&2
}

########
# CHECKS
########

if ! has_creds; then
    echo_stderr "Could not find credentials, please login to AWS before continuing"
    exit 1
fi

if ! check_pcluster_version; then
  echo_stderr "Could not get version, from command 'pcluster version'."
  echo_stderr "ensure pcluster is in your path variable"
  exit 1
fi

if [[ -n "$1" ]] ; then
  cluster_name="$1"
else
	display_help
	exit 1
fi

######
# MAIN
######

# Delete cluster, point to config
pcluster delete \
  --config "${CONDA_PREFIX}/etc/pcluster.conf" \
  "${cluster_name}"
exit 0


