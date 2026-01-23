#!/bin/bash
scp status_check_util.sh baking@132.239.10.$1:/home/baking
ssh baking@132.239.10.$1 'bash -s < /home/baking/status_check_util.sh'
