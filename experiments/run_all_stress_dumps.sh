#!/bin/bash

# Configuration
HOSTS_FILE="pssh_hosts.txt"
#HOSTS_FILE="placeholders.txt"
USER="baking"
SESSION_NAME="stress_test"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

if [ ! -f "$HOSTS_FILE" ]; then
    echo "Error: $HOSTS_FILE not found."
    exit 1
fi

echo "--- Deploying Stress Test with Core Dump Support ---"

while IFS= read -r host || [ -n "$host" ]; do
    host=$(echo "$host" | tr -d '\r' | xargs)
    [[ -z "$host" || "$host" =~ ^# ]] && continue

    echo -n "Targeting $host... "

    if ! ping -c 1 -W 1 "$host" &>/dev/null; then
        echo "OFFLINE"
        continue
    fi

    LOG_FILE="/home/baking/stress_${TIMESTAMP}.log"
    
    # We wrap the command in a subshell that sets the environment locally
    # 1. suid_dumpable=1: Allows sudo processes to dump core
    # 2. ulimit -c unlimited: Removes the size cap for the dump
    CMD="sudo sh -c 'echo 1 > /proc/sys/fs/suid_dumpable; ulimit -c unlimited; /home/baking/easy_bake/testing/probe/run_stress_man.sh fft 20' > $LOG_FILE 2>&1"

    # Launch in tmux
    ssh -n "${USER}@${host}" "tmux new-session -d -s $SESSION_NAME \"$CMD\""

    if [ $? -eq 0 ]; then
        echo "LAUNCHED ✅"
    else
        echo "FAILED ❌"
    fi
done < "$HOSTS_FILE"
