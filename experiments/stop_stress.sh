#!/bin/bash
scp -o ConnectTimeout=5 stop_stress_util.sh baking@132.239.10.$1:/home/baking
ssh -o ConnectTimeout=5 baking@132.239.10.$1 'bash -s < /home/baking/stop_stress_util.sh'
