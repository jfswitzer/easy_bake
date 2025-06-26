#!/bin/bash
DATETIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VOLTAGE=$(vcgencmd measure_volts core)
echo $DATETIME
echo $VOLTAGE
stress-ng --cpu 4 --log-file log.log --cpu-method $1 --verify -v -t $60m 2>&1 | tee ${DATETIME}_${VOLTAGE}_$1_1hr_eb_probe.log
