#!/bin/bash

#set up
unzip spec_archive.zip -d /home/baking
mv spec_archive/* .

./install.sh -f


#post set up
source shrc
runcpu --config=Rpi mcf_r
runcpu --config=Rpi perlbench_r
runcpu --config=Rpi gcc_r
runcpu --config=Rpi xalancbmk_r
#runcpu --config=Rpi leela_r
#runcpu --config=Rpi deepsjeng_r
#runcpu --config=Rpi x264_r
#runcpu --config=Rpi omnetpp_r
