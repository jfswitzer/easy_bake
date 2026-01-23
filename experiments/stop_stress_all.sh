#!/bin/bash
for ip in $(cat ips.txt); do
    ./stop_stress.sh $ip
done
