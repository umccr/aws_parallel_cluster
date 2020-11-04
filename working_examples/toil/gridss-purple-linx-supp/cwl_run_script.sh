#!/usr/bin/env bash

# Get variables as needed
# shellcheck source=/home/ec2-user/env_vars.sh
source "${HOME}/env_vars.sh"

# Conda bug, make sure it's re-sourced in non-interactive mode
# shellcheck source=/home/ec2-user/.conda/etc/profile.d/conda.sh
source "${HOME}/.conda/etc/profile.d/conda.sh"

# Activate conda env
conda activate toil

# Globals
SAMPLE_NAME="$1"
GRIDSS_WORKFLOW_CWL="${HOME}/gridss-purple-linx/cwl/gridss-purple-linx.cwl"
GRIDSS_WORKFLOW_INPUT="${HOME}/input_jsons/${SAMPLE_NAME}.input.json"
BATCH_SYSTEM="slurm"
TOIL_PARTITION="long"
COMPUTE_PARTITION="compute-long"  # Gridss takes too long to run on a spot instance

# Set slurm args to pass
# --no-requeue prevents jobs on spot-instances from restarting, leave it up to toil to do that.
TOIL_SLURM_ARGS="--no-requeue --partition=${COMPUTE_PARTITION}"

# Run config options
retry_count="3"               # Number of times any given job can restart
clean_workdir="onSuccess"
max_local_jobs="8"

# Run sbatch command
sbatch --job-name "toil-gridss-purple-linx-runner" \
       --output "${LOG_DIR}/toil.%j.log" --error "${LOG_DIR}/toil.%j.log" \
       --partition "${TOIL_PARTITION}" \
       --export "TOIL_SLURM_ARGS=${TOIL_SLURM_ARGS},ALL" \
       --wrap "toil-cwl-runner \
                 --jobStore \"${TOIL_JOB_STORE}/job-\${SLURM_JOB_ID}\" \
                 --workDir \"${TOIL_WORKDIR}\" \
                 --outdir \"${TOIL_OUTPUTS}/${SAMPLE_NAME}\" \
                 --batchSystem \"${BATCH_SYSTEM}\" \
                 --writeLogs \"${TOIL_LOG_DIR}\" \
                 --writeLogsFromAllJobs \
                 --runCwlInternalJobsOnWorkers \
                 --maxLocalJobs=\"${max_local_jobs}\" \
                 --cleanWorkDir=\"${clean_workdir}\" \
                 --retryCount=\"${retry_count}\" \
                 \"${GRIDSS_WORKFLOW_CWL}\" \
                 \"${GRIDSS_WORKFLOW_INPUT}\""
