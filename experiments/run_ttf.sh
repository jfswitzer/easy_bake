scp time_to_fail.sh baking@132.239.10.$1:/home/baking
ssh baking@132.239.10.$1 'bash -s < /home/baking/time_to_fail.sh'


