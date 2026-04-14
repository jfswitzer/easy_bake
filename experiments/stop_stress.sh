#!/bin/bash
scp -o ConnectTimeout=5 stop_stress_util.sh baking@$1.dynamic.ucsd.edu:/home/baking
ssh -o ConnectTimeout=5 baking@$1.dynamic.ucsd.edu 'bash -s < /home/baking/stop_stress_util.sh'
