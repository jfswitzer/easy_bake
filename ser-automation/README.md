Setup Pi4
Booted up: uname/pw is baking
Set up firefox
    sudo apt install vim tmux
    git clone http://github.com/jvorob/config.git
    cd config
    bash install_configs.sh ~ # OR SOMETHING

Modify config.txt

# Picocom serial (if using tmux: prefix changes from C-a to 2x C-a) 
To connect:
    picocom -b 115200 /dev/ttyUSB0
To disconnect: C-a C-x   (if using tmux, may need to C-a C-a C-x)
To toggle RTS: C-a C-g
