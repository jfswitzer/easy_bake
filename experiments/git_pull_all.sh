#!/bin/bash
for ip in $(cat ips.txt); do
    scp git_pull.sh baking@132.239.10.$ip:/home/baking 
    ssh baking@132.239.10.$ip 'bash -s < ./git_pull.sh'
done
