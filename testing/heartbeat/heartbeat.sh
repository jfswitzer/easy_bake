#!/bin/sh

# Set log file path
LOGFILE="$HOME/temperature_log.csv"

TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

TEMP=$(vcgencmd measure_temp core)
VOLTAGE=$(vcgencmd measure_volts core)
FREQUENCY_CORE=$(vcgencmd measure_clock core)
FREQUENCY_ARM=$(vcgencmd measure_clock arm)

echo "$TIMESTAMP,$TEMP,$VOLTAGE,$FREQUENCY_CORE,$FREQUENCY_ARM" >> "$LOGFILE"
