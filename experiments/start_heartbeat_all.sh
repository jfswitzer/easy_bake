#!/bin/bash
for ip in $(cat ips.txt); do
    ./start_heartbeat.sh $ip
done
