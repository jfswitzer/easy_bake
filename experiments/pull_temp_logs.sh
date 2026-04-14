#!/bin/bash

for hn in $(cat pssh_hosts.txt); do
    echo $hn
    mkdir -p pulled_temp_logs/$hn
    scp -r baking@$hn:/home/baking/temperature_log.csv pulled_temp_logs/$hn
done
