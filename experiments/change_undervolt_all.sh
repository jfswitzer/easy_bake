#!/bin/bash
for ip in $(cat ips.txt); do
    ./change_undervolt.sh $1 $ip
done
