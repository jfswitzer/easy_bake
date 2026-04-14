#!/bin/bash

HOSTS_FILE="pssh_hosts.txt"
USER="baking"
# The folder where dumps will be stored on each Pi
CORE_DIR="/home/baking/dumps"

echo "--- Enabling Core Dumps across the fleet ---"

while IFS= read -r host || [ -n "$host" ]; do
    host=$(echo "$host" | tr -d '\r' | xargs)
    [[ -z "$host" || "$host" =~ ^# ]] && continue

    echo -n "Configuring $host... "

    # We use a single SSH command to perform all setup steps
    ssh -n "${USER}@${host}" "
        # 1. Create the dump directory
        mkdir -p $CORE_DIR && chmod 777 $CORE_DIR
        
        # 2. Set the core pattern (Kernel level)
        # %e = executable name, %p = pid, %t = timestamp
        echo '$CORE_DIR/core.%e.%p.%t' | sudo tee /proc/sys/kernel/core_pattern
        
        # 3. Make the pattern persistent across reboots
        echo 'kernel.core_pattern=$CORE_DIR/core.%e.%p.%t' | sudo tee /etc/sysctl.d/99-core-dumps.conf
        
        # 4. Set the ulimit to 'unlimited' for the current user in bash
        if ! grep -q 'ulimit -c unlimited' ~/.bashrc; then
            echo 'ulimit -c unlimited' >> ~/.bashrc
        fi
    "

    if [ $? -eq 0 ]; then
        echo "SUCCESS ✅"
    else
        echo "FAILED ❌"
    fi
done < "$HOSTS_FILE"
