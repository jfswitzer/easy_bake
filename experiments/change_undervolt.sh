cp tryboot_template.txt tryboot_scratch.txt
echo "over_voltage=$1" >> tryboot_scratch.txt
echo "over_voltage_min=$1" >> tryboot_scratch.txt

scp tryboot_scratch.txt baking@$2.dynamic.ucsd.edu:/home/baking
scp change_undervolt_rpi.sh baking@$2.dynamic.ucsd.edu:/home/baking
ssh baking@$2.dynamic.ucsd.edu 'bash -s < /home/baking/change_undervolt_rpi.sh'


