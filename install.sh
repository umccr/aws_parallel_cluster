#!/usr/bin/env bash

: '
Simple script that:
1. creates/updates conda env yaml
2. Adds config to etc subdir in <pcluster_conda_prefix>
3. Adds scripts to bin subdir in <pcluster_conda_prefix>
'

###########
# CHECKS
###########
# Check conda is in path; conda --version
# Check jq is in path; jq --version
# echo_stderr command

###########
# GLOBALS
###########
PCLUSTER_CONDA_ENV_NAME="pcluster"

# GET THIS PATH - readlink?

# TODO check if pcluster in envs
# conda env list --json | jq --raw-output '.envs[]' | xargs -I{} basename {}

#########################
# CREATE/UPDATE CONDA ENV
#########################

# if in envs; conda env update --name "${PCLUSTER_CONDA_ENV_NAME}" --file "${CONDA_ENV_FILE}"

# else; conda env create --name "${PCLUSTER_CONDA_ENV_NAME}" --file "${CONDA_ENV_FILE}"

# activate conda env with conda activate "${PCLUSTER_CONDA_ENV_NAME}"

##################
# COPY CONFIG
##################

# cp config.yaml ${CONDA_PREFIX}/etc/config.yaml

###########
# COPY BINS
###########

# rsync --archive bin/ ${CONDA_PREFIX}/bin/