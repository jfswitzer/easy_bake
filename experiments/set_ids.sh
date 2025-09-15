#!/bin/bash
for ip in $(cat ips.txt); do
    echo $ip-1 > scratch.txt
    scp scratch.txt baking@132.239.10.$ip:/home/baking/my_id.txt
done
