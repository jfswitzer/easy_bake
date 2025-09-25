scp kickoff_hb.sh baking@132.239.10.$1:/home/baking
ssh baking@132.239.10.$1 'bash -s < /home/baking/kickoff_hb.sh'
