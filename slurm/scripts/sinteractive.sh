#!/usr/bin/env bash

get_nodes(){
  local partition="$1"
  nodes="$(scontrol show partition "${partition}" --oneliner | {
              tr ' ' '\n'
            } | {
              grep '^Nodes='
            } | {
              cut -d'=' -f2
         })"

  echo "${nodes}"
}

check_nodes(){
  # Check a node is ready
  # 1 for yes, 0 for no
  local nodes="$1"
  node_length=$(scontrol show nodes "${nodes}" --oneliner | grep -v "DRAIN" | grep -cv "No nodes in the system")
  echo "${node_length}"
}

: '
Read in args
'
args="$*"

: '
Get partition
'
DEFAULT_PARTITION="compute"  # FIXME - hardcoded variable
# Get args
while [ $# -gt 0 ]; do
    case "$1" in
        -p|--partition)
          partition="$2"
          shift 1
          ;;
        -p=*|--partition=*)
          partition="${1#*=}"
    esac
    shift
done

if [[ -z "${partition}" ]]; then
  partition="${DEFAULT_PARTITION}"
fi

nodes="$(get_nodes "${partition}")"

if [[ "$(check_nodes "${nodes}")" == "0" ]]; then
  sbatch --wait --partition="${partition}" --wrap "sleep 2" >/dev/null 2>&1
fi

# tcsh implementation adds -l param
if [[ ! "${SHELL}" == "/bin/tcsh" ]]; then
  eval srun "${args}" --pty -u "${SHELL}" -i -l
else
  eval srun "${args}" --pty -u "${SHELL}" -i
fi
