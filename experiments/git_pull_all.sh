#!/bin/bash
for hn in $(cat hostnames.txt); do
    scp git_pull.sh baking@$hn.dynamic.ucsd.edu:/home/baking 
    ssh baking@$hn.dynamic.ucsd.edu 'bash -s < ./git_pull.sh'
done
