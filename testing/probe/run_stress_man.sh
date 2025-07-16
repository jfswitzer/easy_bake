#!/bin/bash
WORKING_DIR="/home/baking/easy_bake/testing/probe"
DATETIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VOLTAGE=$(vcgencmd measure_volts core)
echo $DATETIME
echo $VOLTAGE
stress-ng --cpu 4 --log-file log.log --cpu-method $1 --verify -v -t $2m 2>&1 | tee ${WORKING_DIR}/logs/${DATETIME}_${VOLTAGE}_$1_$2min_eb_probe.log
