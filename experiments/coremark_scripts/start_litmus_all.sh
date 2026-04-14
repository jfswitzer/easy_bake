#!/bin/bash
for ip in $(cat /home/jen/ASPLOS_27/easy_bake/experiments/hostnames.txt); do
    ./start_litmus.sh $ip.dynamic.ucsd.edu
done
