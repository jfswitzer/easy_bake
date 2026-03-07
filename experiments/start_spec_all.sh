#!/bin/bash
for ip in $(cat ips.txt); do
    ./start_spec.sh $1 $ip
done
