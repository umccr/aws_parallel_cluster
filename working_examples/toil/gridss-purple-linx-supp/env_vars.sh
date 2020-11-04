# Used to ensure all env vars are present

# Globals
LOG_DIR="${HOME}/logs"
mkdir -p "${LOG_DIR}"

REF_DIR="${SHARED_DIR}/reference-data"
mkdir -p "${REF_DIR}"

# For download
REF_DIR_HARTWIG="${REF_DIR}/hartwig-nextcloud"
mkdir -p "${REF_DIR_HARTWIG}"

REF_DIR_UMCCR="${REF_DIR}/umccr"
mkdir -p "${REF_DIR_UMCCR}"

INPUT_DIR="${SHARED_DIR}/input-data"
mkdir -p "${INPUT_DIR}"

REF_DIR_BOYLE_LAB="${REF_DIR}/Boyle-Lab"
mkdir -p "${REF_DIR_BOYLE_LAB}"

# For workflow
INPUT_DIR_GRIDSS_PURPLE_LINX_REPO="${INPUT_DIR}/gridss-purple-linx"

# For run instance
TOIL_ROOT="${SHARED_DIR}/toil"
mkdir -p "${TOIL_ROOT}"

TOIL_JOB_STORE="${TOIL_ROOT}/job-store"
TOIL_WORKDIR="${TOIL_ROOT}/workdir"
TOIL_TMPDIR="${TOIL_ROOT}/tmpdir"
TOIL_LOG_DIR="${TOIL_ROOT}/logs"
TOIL_OUTPUTS="${TOIL_ROOT}/outputs"

mkdir -p "${TOIL_JOB_STORE}"
mkdir -p "${TOIL_WORKDIR}"
mkdir -p "${TOIL_TMPDIR}"
mkdir -p "${TOIL_LOG_DIR}"
mkdir -p "${TOIL_OUTPUTS}"

