#!/bin/bash
for ip in $(cat ips.txt); do
    ./execute_testing.sh $ip > $ip-out.log
done
