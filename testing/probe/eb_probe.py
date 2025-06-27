#!/usr/bin/env python3

import sys
import os
import subprocess
import time

# MUST BE RUN AS ROOT
#
# uvolt.status contains either the most recent undervolting amount, in steps (small positive val)
# OR if its time to restart, it contains -1
#
def get_most_recent_log(directory_path='logs'):
    entries = os.listdir(directory_path)
    entries_with_times = []
    for entry in entries:
        if not entry.lower().endswith("probe.log"):
            continue
        full_path = os.path.join(directory_path, entry)
        try:
            modification_time = os.path.getmtime(full_path)
            entries_with_times.append((modification_time, entry))
        except OSError:
            pass 
    sorted_names = [name for time,name in sorted(entries_with_times, key=lambda x: x[0], reverse=True)]
    return sorted_names[0]

def get_uvolt_status():
    try:
        with open("uvolt.status", 'r') as f:
            value = f.read().strip()
        return int(value)
    except Exception as e:
        return None
    
def set_uvolt_status(offset):
    with open("uvolt.status", 'w+') as f:
        f.write(offset)
        return True

def mark_undervolting_done():
    """"Put the current timestamp in a file"""
    current_timestamp = int(time.time())
    with open(".last_time", 'w+') as f:
        f.write(str(current_timestamp))

def check_undervolting_done():
    """Check to make sure that at least 24hr has passed since undervolting was last marked done"""
    with open(".last_time", 'r') as f:
        last_timestamp = f.read().strip()
    diff = abs(int(last_timestamp) - int(time.time()))
    if diff >= 24*3600:
        return True
    else: return False

def restart_uvolt():
    set_uvolt_status(-1)
    mark_undervolting_done()
    
def iterate_undervolt():
    # stop the stress service (it will automatically restart after boot)
    subprocess.Popen(['systemctl','stop','eb_stress'])
    last_uvolt=get_uvolt_status()
    uvolt=0
    if last_uvolt==-1:
        uvolt=0
    else:
        uvolt=last_uvolt+1
    write_tryboot(uvolt)
    set_uvolt_status(uvolt)
    process = subprocess.Popen(['reboot', '\'0 tryboot\''], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def run_experiment():
    """Run the stress experiment"""
    subprocess.Popen(["./run_stress.sh" "fft"])

def check_stress_output():
    """check the output of the stress experiment"""
    logfile=get_most_recent_log()
    with open(logfile, 'r') as file:
        for line in file:
            if "stress-ng: fail:" in line:
                write_macro_log(logfile)
                return True
    return False

#"2025-05-31T09:45:24Z_volt=1.1938V_zeta_10_eb_probe.log"
def write_macro_log(filename):
    err_log="logs/errors.log"
    with open(err_log,"a") as f:
        f.write(f"{filename}\n")
    
def write_tryboot(undervolt_step):
    template="tryboot_template.txt"
    output="/boot/firmware/tryboot.txt"
    placeholder="<voltage>"
    try:
        with open(template, 'r') as f_in:
            content = f_in.read()
        updated_content = content.replace(placeholder, str(undervolt_step))
        with open(output, 'w') as f_out:
            f_out.write(updated_content)

    except FileNotFoundError:
        print(f"Error: Template file not found at '{template}'")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    """Main function of the script."""
    if check_undervolting_done():
        sys.exit()
    
    iterate_undervolt()
    run_experiment()
    err=check_stress_output()
    if err:
       restart_uvolt()

if __name__ == "__main__":
    main()
