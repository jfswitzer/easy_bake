#!/bin/bash

# Define the log file
LOG_FILE="pi_stats.csv"

# Write the CSV header
echo "Iteration,Timestamp,Frequency_MHz,Voltage_V" > "$LOG_FILE"

echo "Starting logs for 1800 iterations..."

for i in $(seq 1 1800)
do
    # Get timestamp
    TIME=$(date date +%Y%m%d_%H%M%S)

    # Extract Frequency (scaled to MHz)
    FREQ=$(vcgencmd measure_clock arm | awk -F= '{printf "%.0f", $2 / 1000000}')

    # Extract Voltage (removes the 'V' suffix)
    VOLT=$(vcgencmd measure_volts core | awk -F= '{print $2}' | sed 's/V//')

    # Log to file
    echo "$i,$TIME,$FREQ,$VOLT" >> "$LOG_FILE"

    # Sleep for 0.1 seconds
    sleep 0.1
done

echo "Done! Stats saved to $LOG_FILE"
