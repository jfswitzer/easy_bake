#/bin/bash

TIMESTAMP=$(date date +%Y%m%d_%H%M%S
)
mkdir litmus_$TIMESTAMP
./run_voltage.sh &
(
sleep 60
./run_coremark.sh
)
wait
mv run1.log litmus_$TIMESTAMP
mv run2.log litmus_$TIMESTAMP
mv pi_stats.csv litmus_$TIMESTAMP
