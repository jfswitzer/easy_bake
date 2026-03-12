#!/bin/bash
WORKING_DIR="/home/jen/ASPLOS_27/easy_bake/testing/probe"
DATETIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VOLTAGE=$(vcgencmd measure_volts core)
echo $DATETIME
echo $VOLTAGE
mkdir -p ${WORKING_DIR}/logs
for i in $(seq 1 $2); do
    echo $i
    (time stress-ng --cpu 4 --log-file log.log --cpu-method $1 --verify --abort -v -t 1m) 2>&1 | tee -a ${WORKING_DIR}/logs/${DATETIME}_${VOLTAGE}_$1_$2min_eb_probe.log
done
