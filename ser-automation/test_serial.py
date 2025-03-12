#!/usr/bin/python3
import argparse
import serial
from enum import Enum
import datetime
import time
import sys
import select
import re
import itertools
import os

OUTPUT_DIR="output_logs"
CSV_NAME="results.csv"

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
  RSLT = 4
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
        return f"<LogEntry #{self.entry_number} {self.timestamp} {self.type.name.upper()}: {self.data}>"

    def __str__(self):
        time = self.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] # we don't need microsec

        # Also: let's make things more legible with some editing
        fmt = self.type.name + ": "
        if self.type == LType.RECV: fmt = "    < "
        if self.type == LType.SEND: fmt = "    > "
        return f"[#{self.entry_number:04}; {time}] {fmt}{self.data}"

class ScrResult:
    "Result of a script run"
    # TODO: split this into timeouts? ERROR results from commands? etc?

    def __init__(self, ok, msg, value=None):
        "If  a result has a sensible value other than Success/Failure, put it in value"
        self.ok = ok
        self.resultValue = value
        self.msg = msg

# Conceptually this is getting closer to a "TestRun" object
# I should try to factor out the serial stuff maybe?
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

        # Meaningful state
        self.results = {}
        # STATE:
        # - runid
        # - config options (config_id n)
        # - boot_ok
        # - genconf_ok
        # - tryboot_ok # Actual result
        # - stress_ok  # Actual result

    # ============= INTERNAL METHODS

    def _addLogEntry(self, entry_type, data):
        timestamp = datetime.datetime.now()
        entry = LogEntry(self.entry_counter, timestamp, entry_type, data)
        self.logEntries.append(entry)
        self.entry_counter += 1

        # TODO: only log if we're in verbose mode?
        print(str(entry))

    def log(self, msg):
        self._addLogEntry(LType.LOG_, msg)
    def dbg(self, msg):
        self._addLogEntry(LType.DBG0, msg)
    def err(self, msg):
        self._addLogEntry(LType.ERR_, msg)

    def recordResult(self, key, value, msg):
        " Records a meaningful bit of state (i.e. will go in results CSV)"
        self.results[key] = value
        self._addLogEntry(LType.RSLT, f"({key}={value}) " + msg)

    def writeOutResults(self):
        """Writes out full log to runid.log, """

        assert "runid" in self.results, "ERROR: can't record results without runid"

        logfile = f"{self.results['runid']}.log"
        #rlogfile = f"{runid}.resultlog"
        csvfile = CSV_NAME
        csvpath =  os.path.join(OUTPUT_DIR, csvfile)



        # === Write results to csv

        # TODO: centralize this / chekc it somehow?
        # All the result columns we're writing to the CSV
        keys = [ "runid", "config_args", "boot_ok", "genconf_ok",
                "tryboot_ok", "stress_test"]
        resultsline = ",".join( str(self.results.get(k,"")) for k in keys)
        self.log(f"Appending results to {csvpath}: {resultsline}")

        # if csv doesn't exist: put in column headers
        if not os.path.exists(csvpath):
            with open(csvpath, "a") as f:
                f.write(",".join(keys) + "\n")


        with open(csvpath, "a") as f:
            f.write(resultsline + "\n")

        logpath =  os.path.join(OUTPUT_DIR, logfile)
        print(f"Writing log to {logpath}")

        #rlogpath = os.path.join(OUTPUT_DIR, rlogfile)
        if os.path.exists(logpath):
            print(f"Error: {logpath} already exists")
            return

        with open(logpath, "w") as outfile:
            for entry in self.logEntries:
                outfile.write(str(entry) + "\n")






    # ============= Serial stuff?


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


    # ============= PUBLIC API (for serial stuff??)

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

    def allLogsToStr(self):
        for entry in self.logEntries:
            self.print_log_entry(entry)


    # Extracts a list of all lines of the given type
    def allOfType(self, ltype):
        return [l for l in self.logEntries if l.type == ltype]
    def allRecv(self): return self.allOfType(LType.RECV)
    def allSend(self): return self.allOfType(LType.SEND)

    # ====

    # Returns last line or None
    def lastSentLine(self):     return (self.allSend() or [None])[-1]
    def lastReceivedLine(self): return (self.allRecv() or [None])[-1]

    #def lastNSentLines(self,n):
    #    " returns last n sent lines, or None "
    #    return list(reversed(itertools.islice(self.lastSentLines(), 0, n)))

    #def lastSentLines(self):
    #    " returns iterator of all sent lines in reverse order "
    #    return filter(lambda x: x.type == LType.SEND, reversed(self.logEntries))

    def checkLastLine(self,pattern):
        " Given a regex, returns true if last line matched this pattern "
        # TODO: generalize this? want to check if
        if self.lastReceivedLine() is None:
            return False
        return re.search(pattern, self.lastReceivedLine().data)

    def runCommandAndCheckOutput(self, cmd, pattern):
        """ sends a command as a string,
        Waits until command completes (i.e. we return to a prompt)
        Checks the second-last line (i.e. last line of output) against pattern

        Returns a failure if the command timed out or if output didn't match pattern
        """

        assert False, "NOT IMPLEMENTED"

        self.send(cmd)
        self.read()
        if not self.checkAtPrompt():
            return # TODO: return failure code

        lastOut = self.allRecv()[-2] # second last line
        if lastOut is None or not re.search(pattern, lastOut.data):
            return # TODO: return failure code

        # Success!
        return # TODO :return success code


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
        #self.read(max_time=60, silent_time=1) #DEBUG: exit quickly
        self.read(max_time=60, silent_time=6)

        # sometimes journald takes a while
        if self.checkLastLine("systemd-journald"):
            # Wait for journal check (takes a while)
            #self.read(max_time=15, silent_time=1) #DEBUG: exit quickly
            self.read(max_time=15, silent_time=15)

        return ScrResult(True, "")
        # TODO: this should check for login msg?

    def scr_Login(self):
        "Call this after boot completes"

        # Because of the tty / systemd bullshit, sometimes it prompts and sometimes it auto-logs in
        if self.checkLastLine("raspberrypi login:"):
            # successfully booted, send uname and pw
            self.send("baking");
            self.read()
            self.send("baking");
            self.read(max_time=10, silent_time=3)
        elif self.checkLastLine("\[press ENTER to login\]"):
            # sometimes it just lets us log in
            self.send("");
            self.read(max_time=10, silent_time=3)
        else:
            self.err("Failed to boot")
            return ScrResult(False, "Boot timed out")

        # Hopefully logged in?
        if not self.checkAtPrompt():
            self.err("Failed to log in")
            return ScrResult(False, "Login Failed")

        #successfully logged in
        self.log("Successfully booted and logged int")
        return ScrResult(True, "Logged in successfully")




    def scr_GenConf(self, conf_id, n):
        self.send("cd ~/easy_bake/ser-automation/tgt_scripts")
        self.read()
        if not self.checkAtPrompt():
            self.err("Command Failed (not at prompt)")
            return ScrResult(False, "cd failed?")

        self.send(f"python3 gen_config.py {conf_id} {n} --out new_tryboot.txt")
        self.read()
        if not self.checkAtPrompt():
            self.err("Command Failed (not at prompt)")
            return ScrResult(False, "gen_config timed out")

        lastOut = self.allRecv()[-2] # second last line
        if lastOut is None or not re.search("BAKE-STEP\|[A-Z_]*\|SUCCESS", lastOut.data):
            self.err("Command Failed (didn't find BAKE-STEP|SUCCESS)")
            return ScrResult(False, "gen_config failed")

        self.send(f"sudo cp new_tryboot.txt /boot/firmware/tryboot.txt"
                  +" && echo 'BAKE-STEP|CP|SUCCESS|'")
        self.read()
        if not self.checkAtPrompt():
            self.err("Command Failed (not at prompt)")
            return ScrResult(False, "sudo cp timed out")
        lastOut = self.allRecv()[-2] # second last line
        if lastOut is None or not re.search("BAKE-STEP\|[A-Z_]*\|SUCCESS", lastOut.data):
            self.err("Command Failed (didn't find BAKE-STEP|SUCCESS)")
            return ScrResult(False, "sudo cp didn't succeed")

        return ScrResult(True, f"Successfully generated config for '{conf_id} {n}'")

    def scr_StressTest(self,iters=4):
      for i in range(iters):
        self.send("stress -c 4 -t 30 && echo 'BAKE-STEP|STRESS|SUCCESS|'")
        self.read(max_time=40, silent_time=35) # Make sure we wait long enough for the run to complete
        if not self.checkAtPrompt():
          self.err("Command Failed (not at prompt)")
          return ScrResult(False, f"stress test prompt failed at iter {i}",value=30*i)
        
        lastOut = self.allRecv()[-2] # second last line
      
        if lastOut is None or not re.search("BAKE-STEP\|[A-Z_]*\|SUCCESS|", lastOut.data):
          self.err("Command Failed (didn't find BAKE-STEP|SUCCESS)")
          return ScrResult(False, f"stress test failed at iter {i}",value=30*i)

      return ScrResult(True, f"Succesfully ran {i} iterations of stress",value=30*iters)
    
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
                else:
                    print(f"Unrecognized command '{user_input[0]}'");

            # Check for serial input (non-blocking)
            while self.ser.in_waiting:
                data = self.ser.readline().decode("utf-8", errors="ignore")
                if data:
                    for line in data.splitlines(keepends=False):
                        print(f"[Received]: '{line}'")


# ================================


# ====== Main


# # ============= TESTING CODE
# def mock_run(self):
#     """Fill in data as if we performed a run, but don't actually
#     do anything with the serial port"""
#     runname = "hello_world"
#     config_id, config_n = "beep", 42
#     assert not " " in runname, "runname should have no spaces"
#     assert not " " in config_id, "config_id should have no space"
#     assert isinstance(config_n, int), "n should be an int"
#     runid = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "-" + str(runname)
#     self.recordResult("runid", runid, "Starting run")
#     self.recordResult("config_args", f"{config_id} {config_n}", "")
#
#     self.recordResult("boot_ok", True, "foo")
#
#     self.recordResult("genconf_ok", False, "bar")
# # ============= END TESTING CODE


def tryRun(self, runname, config_id, config_n):
    assert not " " in runname, "runname should have no spaces"
    assert not " " in config_id, "config_id should have no space"
    assert isinstance(config_n, int), "n should be an int"

    runid = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + str(runname)
    self.recordResult("runid", runid, " === Starting run ===")
    self.recordResult("config_args", f"{config_id} {config_n}", "")

    self.reboot()

    self.scr_AwaitBoot()

    res = self.scr_Login() #Log in to pi
    self.recordResult("boot_ok", res.ok, res.msg)
    if not res.ok:
        return


    res = self.scr_GenConf(config_id, 0)
    self.recordResult("genconf_ok", res.ok, res.msg)
    if not res.ok:
        return

    # ==== All generated, now time to reboot
    # (return here if we want to just boot and debug interactively)

    serint.scr_Tryboot()
    serint.scr_AwaitBoot()
    res = serint.scr_Login() #Log in to pi
    self.recordResult("tryboot_ok", res.ok, res.msg)
    if not res.ok:
        return

    res_stress = serint.scr_StressTest()
    self.recordResult("stress_test",res_stress.resultValue, res_stress.msg)
    if not res_stress.ok:
      return

parser=argparse.ArgumentParser()
parser.add_argument("config_id",help="name of the config file to run")
args=parser.parse_args()
for i in range(9):
    # new main
    print(f"\n==== STARTING RUN {i} ===\n\n")
    serint = SerialInterface(DEV)
    serint.open()
    serint.reboot()
    config=args.config_id
    print(f"\n CONFIG ID: {config}\n")
    tryRun(serint, "test_debug", config, i)
    #serint.read(max_time=10)

    print("\n\n\n==== RUN RESULTS ===")
    print(serint.results)
    serint.writeOutResults()

    serint.close()


#mock_run(serint)


# # go interactive
# serint.console()


