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

############
# CONDA
############

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

###########
# GLOBALS
###########

PCLUSTER_CONDA_ENV_NAME="pcluster"
CONDA_ENV_FILE="$(get_this_path)/conf/pcluster-env.yaml"

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

#########################
# CREATE/UPDATE CONDA ENV
#########################

if ! has_conda_env; then
  echo_stderr "pcluster conda env does not exist. Creating"
  conda env create \
    --quiet \
    --name "${PCLUSTER_CONDA_ENV_NAME}" \
    --file "${CONDA_ENV_FILE}"
else
  echo_stderr "Found conda env 'pcluster' - running update"
  conda env update \
    --quiet \
    --name "${PCLUSTER_CONDA_ENV_NAME}" \
    --file "${CONDA_ENV_FILE}"
fi

# Now we can obtain the env prefix which is where we will place our
conda_pcluster_env_prefix="$(get_conda_env_prefix)"

##################
# COPY CONFIG
##################

echo_stderr "Adding pcluster.conf to \"${conda_pcluster_env_prefix}/etc/pcluster.conf\""
mkdir -p "${conda_pcluster_env_prefix}/etc/"
cp "$(get_this_path)/conf/pcluster.conf" "${conda_pcluster_env_prefix}/etc/pcluster.conf"

# Ensure that if we're installing from the git repo, that we turn '__VERSION__' into 'latest'
sed -i "s/__VERSION__/latest/g" "${conda_pcluster_env_prefix}/etc/pcluster.conf"

###########
# COPY BINS
###########

echo_stderr "Adding scripts to \"${conda_pcluster_env_prefix}/bin\""
# Ensure all the scripts are executable
chmod +x "$(get_this_path)/bin/*.sh"
rsync --archive \
  --include='*.sh' --exclude='*'\
  "$(get_this_path)/bin/" "${conda_pcluster_env_prefix}/bin/"

echo_stderr "Installation Complete!"

################
# PROMPT_COMMAND
################

: '
Something a little fancy - shows pcluster version on ps1
'

mkdir -p "${conda_pcluster_env_prefix}/etc/conda/activate.d/"
mkdir -p "${conda_pcluster_env_prefix}/etc/conda/deactivate.d/"

# Activate
{
  echo -e "#!/usr/bin/env bash"
  echo -e "if [[ ! -v PROMPT_COMMAND ]]; then"
  echo -e "\t export PROMPT_COMMAND==\"printf ' __VERSION__ '\""
  echo -e "else"
  echo -e "\t export DO_NOT_UNSET_PROMPT_COMMAND=true"
  echo -e "fi"
} > "${conda_pcluster_env_prefix}/etc/conda/activate.d/prompt.sh"

# Deactivate
{
  echo -e "#!/usr/bin/env bash"
  echo -e "if [[ ! -v DO_NOT_UNSET_PROMPT_COMMAND ]]; then"
  echo -e "\t unset PROMPT_COMMAND"
  echo -e "else"
  echo -e "\t unset DO_NOT_UNSET_PROMPT_COMMAND"
  echo -e "fi"
} > "${conda_pcluster_env_prefix}/etc/conda/deactivate.d/prompt.sh"
