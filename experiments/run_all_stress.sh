#!/bin/bash

# Configuration
HOSTS_FILE="pssh_hosts.txt"
#HOSTS_FILE="placeholders.txt"
USER="baking"
SESSION_NAME="stress_test"

# Generate a single timestamp for this "batch" of runs
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

if [ ! -f "$HOSTS_FILE" ]; then
    echo "Error: $HOSTS_FILE not found."
    exit 1
fi

echo "--- Starting Global Deployment ($TIMESTAMP) ---"

while IFS= read -r host || [ -n "$host" ]; do
    host=$(echo "$host" | tr -d '\r' | xargs)
    [[ -z "$host" || "$host" =~ ^# ]] && continue

    echo -n "Targeting $host... "

    if ! ping -c 1 -W 1 "$host" &>/dev/null; then
        echo "OFFLINE"
        continue
    fi

    # The magic: We wrap the command in a subshell that redirects output to a file
    # This file will be saved in /home/baking/ on each Pi.
    LOG_FILE="/home/baking/stress_${TIMESTAMP}.log"
    CMD="ulimit -c unlimited; sudo /home/baking/easy_bake/testing/probe/run_stress_man.sh fft 20 > $LOG_FILE 2>&1"

    # Launch detached tmux session
    ssh -n "${USER}@${host}" "tmux new-session -d -s $SESSION_NAME \"$CMD\""

    if [ $? -eq 0 ]; then
        echo "LAUNCHED (Log: $LOG_FILE) ✅"
    else
        echo "FAILED ❌"
    fi
done < "$HOSTS_FILE"

echo "--- All commands dispatched ---"
