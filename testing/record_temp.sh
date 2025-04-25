#!/bin/sh

# Set log file path
LOGFILE="$HOME/temperature_log.txt"

# Set interval in seconds (e.g., every 60 seconds)
INTERVAL=1

echo "Logging temperature to $LOGFILE every $INTERVAL seconds."
echo "Press [CTRL+C] to stop."

while true; do
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    TEMP_OUTPUT=$(vcgencmd measure_temp core)
    echo "$TIMESTAMP - $TEMP_OUTPUT" >> "$LOGFILE"
    sleep $INTERVAL
done
