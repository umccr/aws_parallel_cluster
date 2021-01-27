#!/usr/bin/env bash

: '
Simple script that:
1. creates/updates conda env yaml
2. Adds config to etc subdir in <pcluster_conda_prefix>
3. Adds scripts to bin subdir in <pcluster_conda_prefix>
'

# Ensure installation fails on non-zero exit code
set -euo pipefail

###########
# GLOBALS
###########

PCLUSTER_CONDA_ENV_NAME="pcluster"
REQUIRED_CONDA_VERSION="4.9.0"

###########
# CHECKS
###########

echo_stderr() {
  echo "$@" 1>&2
}

has_conda() {
  if ! conda --version >/dev/null; then
    echo_stderr "Could find command 'conda'. Please ensure conda is installed before continuing"
    return 1
  fi
}

has_jq() {
  if ! jq --version >/dev/null; then
    echo_stderr "Could not find command 'jq'. Please ensure jq is installed before continuing"
    return 1
  fi
}

check_readlink_program() {
  if [[ "${OSTYPE}" == "darwin"* ]]; then
    readlink_program="greadlink"
  else
    readlink_program="readlink"
  fi

  if ! type "${readlink_program}"; then
      if [[ "${readlink_program}" == "greadlink" ]]; then
        echo_stderr "On a mac but 'greadlink' not found"
        echo_stderr "Please run 'brew install coreutils' and then re-run this script"
        return 1
      else
        echo_stderr "readlink not installed. Please install before continuing"
      fi
  fi
}

get_this_path() {
  : '
  Mac users use greadlink over readlink
  Return the directory of where this install.sh file is located
  '
  local this_dir

  # darwin is for mac, else linux
  if [[ "${OSTYPE}" == "darwin"* ]]; then
    readlink_program="greadlink"
  else
    readlink_program="readlink"
  fi

  # Get directory name of the install.sh file
  this_dir="$(dirname "$("${readlink_program}" -f "${0}")")"

  # Return directory name
  echo "${this_dir}"
}

_verlte() {
  [ "$1" = "$(echo -e "$1\n$2" | sort -V | head -n1)" ]
}

_verlt() {
  [ "$1" = "$2" ] && return 1 || verlte "$1" "$2"
}

############
# CONDA
############

get_conda_version() {
  local version
  version="$(conda --version | cut -d' ' -f2)"

  echo "${version}"
}

has_conda_env() {
  : '
  Check if a conda environment exists
  '
  local conda_envs
  local conda_env_path

  conda_envs="$(conda env list \
                  --json \
                  --quiet | {
                jq --raw-output '.envs[]'
               })"

  for conda_env_path in ${conda_envs}; do
    if [[ "$(basename "${conda_env_path}")" == "${PCLUSTER_CONDA_ENV_NAME}" ]]; then
      # Conda env has been found
      return 0
    fi
  done
  # Conda env was not found
  return 1
}

get_conda_env_prefix() {
  : '
  Get the prefix of a conda environment
  '

  local conda_env_prefix

  conda_env_prefix="$(conda env export \
                        --name "${PCLUSTER_CONDA_ENV_NAME}" \
                        --json | {
                      jq '.prefix' \
                        --raw-output
                    })"

  # Should return something like '/home/alexiswl/anaconda3/envs/pcluster'
  echo "${conda_env_prefix}"
}

check_conda_version() {
  : '
  Make sure at the latest conda version
  '
  if ! _verlte "${REQUIRED_CONDA_VERSION}" "$(get_conda_version)"; then
    echo_stderr "Your conda version is too old"
    return 1
  fi
}

############
# RUN CHECKS
############

# Installations
echo_stderr "Checking conda and jq are installed"

if ! has_conda; then
  echo_stderr "Error, could not find conda binary."
  echo_stderr "Please install conda and ensure it is in your \"\$PATH\" environment variable before continuing"
  exit 1
fi

if ! has_jq; then
  echo_stderr "Error, could not find jq binary."
  echo_stderr "Please install jq globally (preferred) via apt/brew or locally via conda before continuing"
  exit 1
fi

if ! check_conda_version; then
  echo_stderr "Your conda version is out of date, please run \"conda update -n base -c defaults conda\" before continuing"
  exit 1
fi

if ! check_readlink_program; then
  echo_stderr "Failed at readlink check stage"
  exit 1
fi

##########################################
# Strip __AWS_PARALLEL_CLUSTER_VERSION__
##########################################

: '
Only needed in the event that one is installing from source
in which case we dont have a clue what version to install, therefore we eradicate it completely
'

# Create alternative source file
conda_env_file="$(get_this_path)/conf/pcluster-env.yaml"

if [[ "${OSTYPE}" == "darwin"* ]]; then
  tmp_conda_env_file="$(mktemp -t "conda.env.").yaml"
else
  tmp_conda_env_file="$(mktemp --suffix ".conda.env.yaml")"
fi

# Swap out "aws-parallelcluster == __AWS_PARALLEL_CLUSTER_VERSION__"
# for aws-parallelcluster
sed "s/aws-parallelcluster == __AWS_PARALLEL_CLUSTER_VERSION__/aws-parallelcluster/" \
  "${conda_env_file}" > "${tmp_conda_env_file}"
# FIXME - scope for getting this value rather than ignoring it
# TAG_REGEX='^refs\/tags\/(?:pre-)?v(\d+\.\d+\.\d+)-(?:\d+\.\d+\.\d+)$'
# determine if we're in the right git repo?
# get the current checkout tag, match it to a versioned tag -> might need to go remote
# strip the refs/tags etc replace


#########################
# CREATE/UPDATE CONDA ENV
#########################

if ! has_conda_env; then
  echo_stderr "pcluster conda env does not exist - would you like to create one?"
    select yn in "Yes" "No"; do
    case "$yn" in
        "Yes" )
          conda env create \
            --quiet \
            --name "${PCLUSTER_CONDA_ENV_NAME}" \
            --file "${tmp_conda_env_file}"
          break;;
        "No" )
          echo_stderr "Installation cancelled"
          exit 0;;
    esac
  done

else
  echo_stderr "Found conda env 'pcluster' - would you like to run an update?"
  select yn in "Yes" "No"; do
    case "$yn" in
        "Yes" )
          conda env update \
            --quiet \
            --name "${PCLUSTER_CONDA_ENV_NAME}" \
            --file "${tmp_conda_env_file}"
          break;;
        "No" )
          echo_stderr "Installation cancelled"
          exit 0;;
    esac
  done
fi

# Now we can obtain the env prefix which is where we will place our
conda_pcluster_env_prefix="$(get_conda_env_prefix)"

###########
# COPY BINS
###########

echo_stderr "Adding python scripts to \"${conda_pcluster_env_prefix}/bin\""
# Ensure all the scripts are executable
find "$(get_this_path)/bin/" \
  -mindepth 1 -maxdepth 1 \
  -type f -name "*.py" \
  -exec chmod +x {} \;

# Copy over to conda env
rsync --archive \
  --include='*.py' --exclude='*' \
  "$(get_this_path)/bin/" "${conda_pcluster_env_prefix}/bin/"

###########
# COPY LIBS
###########

# Copy over umccr_utils to library path
rsync --archive \
  --include='*.py' --exclude='*' \
  "$(get_this_path)/lib/umccr_utils/" "${conda_pcluster_env_prefix}/lib/python3.8/umccr_utils/"

#####################
# REPLACE __VERSION__
#####################

: '
Only needed in the event that one is installing from source
'

sed "s/__VERSION__/latest/" \
  "${conda_pcluster_env_prefix}/lib/python3.8/umccr_utils/version.py" > \
  "${conda_pcluster_env_prefix}/lib/python3.8/umccr_utils/version.py.tmp"

mv "${conda_pcluster_env_prefix}/lib/python3.8/umccr_utils/version.py.tmp" \
  "${conda_pcluster_env_prefix}/lib/python3.8/umccr_utils/version.py"


###############
# END OF SCRIPT
###############
echo_stderr "Installation Complete!"

