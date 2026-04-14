scp kickoff_hb.sh baking@$1.dynamic.ucsd.edu:/home/baking
ssh baking@$1.dynamic.ucsd.edu 'bash -s < /home/baking/kickoff_hb.sh'
