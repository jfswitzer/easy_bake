#!/bin/bash
for ip in $(cat ips.txt); do
    scp reload_daemon.sh baking@132.239.10.$ip:/home/baking
    ssh baking@132.239.10.$ip 'bash -s < ./reload_daemon.sh'
done
