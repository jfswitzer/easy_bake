#!/usr/bin/python3

import serial
from enum import Enum
import datetime
import time
import sys
import select
import re

# ================ TODOS
# (on pi)
# - move the config_and_reboot into a bash script
# - move the stress test into a bash script
#
# (on host):
# - write a "run_command" that runs, waits until prompt (or timeout),
#   - returns a result code (got back to prompt or timed out)
#   - returns a list of output entries (for checking success condition?)
# - write a "dump logs to file"
# - add a test/result logentry? (i.e. TEST: run_id=[test_sweep 0], TEST: result=[booted, true])
#   - dump results to CSV

# Refactors / improvements:
# - switch to event loop, so reading happens automatically?
# - have boot run faster (i.e. when it sees journald, wait until boot screen shows up)
# - don't auto-power cycle (so can edit/rerun code without waiting for reboot)
#   - might need to put a capacitor on global_en to handle transients??

# Variable Constants? (Config Constants?)
DEV = '/dev/ttyUSB0'

# Constants
END_ANSI = "\033[0m"
MB = 1024 * 1024


ser = serial.Serial(None, 115200,
                timeout=0.25, rtscts=False, dsrdtr=False)

# ================================

class LType(Enum):
  RECV = 1
  SEND = 2
  LOG_ = 3
  ERR_ = 10 # Debug levels: 0 is almost always too verbose
  DBG0 = 20 # Debug levels: 0 is almost always too verbose
            #               10 is almost always shown

class LogEntry:
    def __init__(self, entry_number, timestamp, entry_type, data):
        self.entry_number = entry_number
        self.timestamp = timestamp
        self.type = entry_type
        self.data = data

    def __repr__(self):
        return f"[{self.entry_number}] {self.timestamp} {self.type.name.upper()}: {self.data}"

class ScrResult:
    "Result of a script run"
    # TODO: split this into timeouts? ERROR results from commands? etc?

    def __init__(self, ok, msg):
        self.ok = ok
        self.msg = msg

class SerialInterface:
    def __init__(self, port, baudrate=115200, timeout=0.25):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        #self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.ser = serial.Serial(None, baudrate,
                   timeout=timeout, rtscts=False, dsrdtr=False)
        self.logEntries = []
        self.entry_counter = 0

    # ============= INTERNAL METHODS

    def _addLogEntry(self, entry_type, data):
        timestamp = datetime.datetime.now()
        entry = LogEntry(self.entry_counter, timestamp, entry_type, data)
        self.logEntries.append(entry)
        self.entry_counter += 1

        # TODO: only log if we're in verbose mode?
        self.print_log_entry(entry)

    def log(self, msg):
        self._addLogEntry(LType.LOG_, msg)
    def dbg(self, msg):
        self._addLogEntry(LType.DBG0, msg)
    def err(self, msg):
        self._addLogEntry(LType.ERR_, msg)


    def setPower(self, power_en):
        """ Powers the RaspPi on or off by setting the RTS Pin"

        Note: RTS~ is active-low, and is wired into GLOBAL_EN,
        so RTS=0 enables power, RTS=1 cuts it"""
        if power_en:
            self.ser.rts = 0 # Active low, RTS=0 pulls GLOBAL_EN high
        else:
            self.ser.rts = 1 # Drives RTS low, cuts power to Pi

        # TODO: hide this behind a verbosity thing?
        powerstr = "ON" if power_en else "OFF"
        self.log(f"Setting POWER={powerstr}");


    # ============= PUBLIC API

    def reboot(self) :
        self.setPower(False)
        time.sleep(0.25)
        self.setPower(True)

    def open(self, power_en=True):
        """ Note: by default, when the DFRobot usb-serial adapter
        is plugged in with no serial port open, RTS~
        is high (i.e. rasp-pi is on). Opening a port drives RTS~ to
        active-low, which sets global_en low, which cuts power to the RaspPi.

        Passing in power_en=True will try to keep RTS off, hopefully
        not power-cycling the Pi, (but it seems that doesn't always succeed)"""

        self.ser.port = DEV
        self.setPower(power_en) # set power level before opening port
                           # so it opens with correct RTS state
        powerstr = "ON" if power_en else "OFF"
        self.log(f"Opening port {DEV}, power={powerstr}");
        self.ser.open()

    def send(self, data):
        "Sends data, followed by a newline"
        #if not self.ser.is_open:
        #    self.ser.open()
        self.ser.write((data + '\n').encode('utf-8'))
        self._addLogEntry(LType.SEND, data)

    def read(self, max_time=5, silent_time=1):
        """ Try to read data for up to a certain number of seconds.
        Will stop reading once it goes timeout seconds without any
        data, or when it hits max_time or MAX_DATA

        Returns True if timed out (too much data)
        """
        MAX_DATA = 1 * MB
        MAX_TIMEOUT = max_time
        SILENT_TIMEOUT = silent_time
        SLEEP_INTERVAL = 0.05 # 50ms
        #if not self.ser.is_open:
        #    self.ser.open()

        start_time = time.time()
        last_data = time.time()

        self.dbg(f"Reading: max time {MAX_TIMEOUT}s, gap time {SILENT_TIMEOUT}s")

        while True:
            elapsed_time = time.time() - start_time

            if elapsed_time > MAX_TIMEOUT:
                self.dbg(f"read timed out: {elapsed_time}s elapsed")
                return True # timed out: too much data

            # if
            #if self.ser.in_waiting:


            self.ser.timeout = SLEEP_INTERVAL
            line = self.ser.readline();
            # Note: readline will go until it hits a \n or times out
            # If it times out, it will return a partial line

            if line:
                last_data = time.time()
                if line.endswith(b"\n"):
                    line = line[:-1]
                line = line.decode('utf-8', errors='replace')
                self._addLogEntry(LType.RECV, line)
            else:
                # No data, let's sleep for a bit
                elapsed_since_data = time.time() - last_data
                if elapsed_since_data > SILENT_TIMEOUT:
                    # We haven't had any data in a while, other
                    # end isprobably done sending
                    self.dbg(f"read timed out: {elapsed_since_data:.1f}s with no data")
                    return False

                # no data: let's keep sleeping
                time.sleep(SLEEP_INTERVAL)

        #data += self.ser.read(self.ser.in_waiting)

    def close(self):
        if self.ser.is_open:
            self.ser.close()
        self.log("Serial connection closed")

    def print_log_entry(self, e):
        # time goes
        #time = e.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
        time = e.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] # we don't need microsec

        # Also: let's make things more legible with some editing
        fmt = e.type.name + ": "
        if e.type == LType.RECV: fmt = "    < "
        if e.type == LType.SEND: fmt = "    > "
        print(f"[#{e.entry_number:04}; {time}] {fmt}{e.data}")

    def print_all_log_entries(self):
        for entry in self.logEntries:
            self.print_log_entry(entry)

    def print_last_received(self, n):
        lastRecvRev = [e for e in reversed(self.logEntries) if e.type == LType.RECV]
        lastN = reversed(lastRecvRev[:n])
        # TODO: separate out the selecting and the printing?
        # TODO: I should just make a thing to get all received lines and do [-n:]
        for entry in lastN:
            self.print_log_entry(entry)
    def lastReceivedLine(self):
        " returns  last received line, or None "
        for line in reversed(self.logEntries):
            if line.type == LType.RECV:
                return line
        return None

    def lastSentLine(self):
        " returns  last sent line, or None "
        for line in reversed(self.logEntries):
            if line.type == LType.SEND:
                return line
        return None

    def checkLastLine(self,pattern):
        " Given a regex, returns true if last line matched this pattern "
        # TODO: generalize this? want to check if
        if self.lastReceivedLine() is None:
            return False
        return re.search(pattern, self.lastReceivedLine().data)

    # ================= BUILDING BLOCKS ======================

    def checkAtPrompt(self, promptstr="baking@raspberrypi:.*\$"):
        " Makes sure we've gotten a prompt since the last command we sent"
        # TODO: generalize this? want to check if
        lSent = self.lastSentLine()
        lRecv = self.lastReceivedLine()

        if lRecv is None:
            return False # none received means no prompt

        if lSent is not None and lSent.entry_number > lRecv.entry_number:
            return False # none received since last sent command

        return self.checkLastLine(promptstr)

    # ================= HIGH LEVEL BLDG BLOCKS ======================

    #def runCommand():

    # ================= SCRIPTS ======================
    # A specific task: i.e. generate a series of commands, listen for responses,
    # return a ScrResult

    def scr_AwaitBoot(self):
        " "
        # Read for the full boot time
        self.read(max_time=60, silent_time=6)

        # sometimes journald takes a while
        if self.checkLastLine("systemd-journald"):
            # Wait for journal check (takes a while)
            self.read(max_time=15, silent_time=15)

        return ScrResult(True, "")
        # TODO: this should check for login msg?

    def scr_Login(self):
        "Call this after boot completes"

        if self.checkLastLine("raspberrypi login:"):
            # successfully booted
            self.send("baking");
            self.read()
            self.send("baking");
            self.read(max_time=10, silent_time=3)
        elif self.checkLastLine("\[press ENTER to login\]"):
            #oops, this happens sometimes
            self.send("");
            self.read(max_time=10, silent_time=3)
        else:
            self.err("Failed to boot: last lines are:")
            self.print_last_received(5)
            return ScrResult(False, "Boot timed out")

        # Hopefully logged in?
        if not self.checkAtPrompt():
            #successfully logged in
            self.log("Successfully booted and logged int")
            return ScrResult(True, "")
        else:
            self.err("Failed to log in: last lines are:")
            self.print_last_received(5)
            return ScrResult(False, "Login Failed")




    def scr_GenConf(self, conf_id, n):
        self.send("cd ~/easy_bake/ser-automation/tgt_scripts")
        self.read()
        if not self.checkAtPrompt():
            self.err("Command Failed (not at prompt)")
            return

        self.send(f"python3 gen_config.py {conf_id} {n} --out new_tryboot.txt")
        self.read()
        if not self.checkAtPrompt():
            self.err("Command Failed (not at prompt)")
            return
        # TODO: CHECK FOR ERROR OUTPUT

        self.send(f"sudo cp new_tryboot.txt /boot/firmware/tryboot.txt")
        self.read()
        if not self.checkAtPrompt():
            self.err("Command Failed (not at prompt)")
            return


    def scr_Tryboot(self):
        self.send(f"sudo reboot '0 tryboot'")
        pass



    # ================================================

    def console(self):
        " just pass user input to / from the serial port "
        while True:
            # Check for user input (non-blocking)
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                user_input = sys.stdin.readline().strip().split()

                if len(user_input) == 0:
                    continue
                elif user_input[0] == "exit":
                    print("Exiting serial monitor...")
                    self.ser.close()
                    break
                elif user_input[0] == "send":
                    cmd = " ".join(user_input[1::])
                    print(f"DEBUG: cmd is '{cmd}'")
                    self.ser.write((cmd + "\n").encode("utf-8"))
                elif user_input[0] == "pulse":
                    self.ser.rts = 1; # RTS=1 sets it low (pulls down GLB_EN)
                    time.sleep(1);
                    self.ser.rts = 0;
                    time.sleep(1);
                elif user_input[0] == "run":
                    # put together the rest of the args, parse them as an int
                    n_str = " ".join(user_input[1::]).strip()
                    try:
                        n = int(n_str)
                        self.scr_GenConf("test_sweep", n)
                    except ValueError:
                        print(f"Can't parse int '{n_str}'")
                else:
                    print(f"Unrecognized command '{user_input[0]}'");

            # Check for serial input (non-blocking)
            while self.ser.in_waiting:
                data = self.ser.readline().decode("utf-8", errors="ignore")
                if data:
                    for line in data.splitlines(keepends=False):
                        print(f"[Received]: '{line}'")


# ================================


# See serial docs here:
#   https://pythonhosted.org/pyserial/pyserial_api.html

# def old_main() :
#     print(" ==== Created Serial Object");
#     time.sleep(0.5);
#     ser.port = DEV
#     ser.rts = 1 # setting this to 0 pulls it high?
#     ser.open()
#     print(" ==== Opened port: RTS 1");
#     time.sleep(0.5);
#     print(f"Opened port {ser.name}");
#     ser.rts = 0 # setting this to 0 pulls it high?
#                 # My little circuit ties RTS to GLOBAL_EN, so pulling
#                 # RTS low reboots the chip
#     #ser.open();
#     print("===== Setting RTS to 0")
#     time.sleep(0.5);
#
#     print("===== Reading initial text...")
#     s = ser.read(64000);
#     print("===== Initial text: {\n" + s.decode('utf8', errors="ignore") + "===== }" +  END_ANSI);
#     print("===== Writing command:");
#     ser.write(b'ls\n');
#     s = ser.read(64000);
#     print("===== Got response:\n" + s.decode('utf8', errors="ignore") + "=====" + END_ANSI);
#
#
#     #ser.rts = 1;
#     #time.sleep(1);
#     #ser.rts = 0;
#     #time.sleep(1);
#
#     while True:
#         # Check for user input (non-blocking)
#         if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
#             user_input = sys.stdin.readline().strip().split()
#
#             if len(user_input) == 0:
#                 continue
#             elif user_input[0] == "exit":
#                 print("Exiting serial monitor...")
#                 ser.close()
#                 break
#             elif user_input[0] == "send":
#                 cmd = " ".join(user_input[1::])
#                 print(f"DEBUG: cmd is '{cmd}'")
#                 ser.write((cmd + "\n").encode("utf-8"))
#             elif user_input[0] == "pulse":
#                 ser.rts = 1; # RTS=1 sets it low (pulls down GLB_EN)
#                 time.sleep(1);
#                 ser.rts = 0;
#                 time.sleep(1);
#             else:
#                 print(f"Unrecognized command '{user_input[0]}'");
#
#         # Check for serial input (non-blocking)
#         while ser.in_waiting:
#             data = ser.readline().decode("utf-8", errors="ignore")
#             if data:
#                 for line in data.splitlines(keepends=False):
#                     print(f"[Received]: '{line}'")
#
#
#     ser.close();
# # End of old main


# ====== RUN STUFF:

class RunInfo:
    def __init__(self, runname, config_id, n):
        self.runid = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + str(runname)
        self.config_id = config_id
        self.run_n = n

    def logFileName(self):
        return f"{runid}.log"

    def logFileName(self):
        return f"{runid}.log"

# ===

res_bootSucc=False
res_trybootSucc=False
res_stressSucc=False

res_otherErr=False

# new main
serint = SerialInterface(DEV)
serint.open()
serint.reboot()
#serint.read(max_time=10)

serint.scr_AwaitBoot()

serint.scr_Login() #Log in to pi

serint.send("ls")
serint.read()
# === TODO: test that we logged in successfully
res_bootSucc=True

serint.scr_GenConf("test_sweep", 0)

serint.scr_Tryboot()
serint.scr_AwaitBoot()
serint.scr_Login() #Log in to pi

# go interactive
serint.console()


