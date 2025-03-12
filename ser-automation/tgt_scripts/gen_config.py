# Used to set up the next configuration to test

import sys
import argparse
from enum import Enum


def err(msg):
    print(f"Error: {str(msg)}")
def err_exit(msg, code=1):
    err(msg)
    raise SystemExit(code) from None # needed to exit from inside exception handlers

#print(f"Got arg {args.config_id}")

class CT(Enum): #ConfType
    STATIC = 0
    FUNC = 1 # a function that returns a list of var dicts


def genVars1():
    """ returns a list of {"VOLTAGE":n, "FREQUENCY": n} """
    confs = []
    for v in range(-16,4):
        for f in [1200,1250,1300]:
            confs.append({"VOLTAGE": v, "FREQUENCY": f})
    return confs

def genVarsPi3B():
    """ returns a list of {"VOLTAGE":n, "FREQUENCY": n} """
    confs = []
    for v in range(-3,2):
        for f in range(1200,1350,20):
            confs.append({"VOLTAGE": v, "FREQUENCY": f})
    return confs

configs = {
        "test_static": {
          "_template": "tryboot_template.txt",
          "_vars": (CT.STATIC, { "VOLTAGE": 1, "FREQUENCY": 2 })
            # vary from -10 to 4
        },
        "test_sweep": {
          "_template": "tryboot_template.txt",
          "_vars": (CT.FUNC, genVars1)
            # vary from -10 to 4
        },
        "test_3b": {
          "_template": "tryboot_template.txt",
          "_vars": (CT.FUNC, genVarsPi3B)
        }
}

class Config:
    def __init__(self, id):
        #loads config with given id
        self.id = id

        if id not in configs:
            err_exit(f"Config {id} not recognized")

        _conf = configs[id]
        self.template_file = _conf['_template']

        self.varType, self.varObj = _conf["_vars"]
        if not isinstance(self.varType, CT):
            print(f"Bad config type {repr(self.varType)}")


        #print(f"Loading template file {self.template_file}")
        try:
            with open(self.template_file) as f:
                self.template_str = f.read()
        except IOError as e:
            err_exit(f"I/O error: {e}")
        except Exception as e: #handle other exceptions such as attribute errors
            err_exit("Unexpected error:", e)

        if not self.template_str:
            err_exit(f"Template file {self.template_file} is empty")

    def numRuns(self):
        if self.varType == CT.STATIC:
            return 1
        elif self.varType == CT.FUNC:
            confs = self.varObj()
            return len(confs)
        else:
            err_exit(f"ASSERT FAILED: unexpected config tpe {self.varType}");

    def getAllVars(self):
        if self.varType == CT.STATIC:
            return [self.varObj]
        elif self.varType == CT.FUNC:
            return self.varObj()
        else:
            err_exit(f"ASSERT FAILED: unexpected config tpe {self.varType}");

    def genConf(self, n):
        " Gen the config file for run n"

        allVars = self.getAllVars()
        try:
            currVars = allVars[n]
        except Exception as e:
            print(repr(e))
            err_exit(f"Invalid run #{n}, config '{self.id}' only goes up to n={len(allVars)-1}")

        try:
            result = self.template_str.format_map(currVars)
        except ValueError as e:
            err_exit("Template contains positional field (e.g. {})")
        except KeyError as e:
            err_exit(f"Template contains unexpected variable {e.args[0]}")
        return result





def listConfs():
    print("Listing Configs:")
    for conf_id in configs.keys():
        conf = Config(conf_id)
        n = conf.numRuns()
        print(f" {conf_id} : 0-{n-1}")

# ==================== MAIN

parser = argparse.ArgumentParser(prog="gen_config.py",
            description="""Generates config files for automated stress testing:
there's different kinds of configs (specified as a dictionary in the source.
Each config has a string id, and generates 1 or more runs

    `gen_config.py CONFIG_ID N --out outfile.txt /boot/firmware/tryboot.txt`

You should run gen_config once for N ranging from 0 to $MAX_N
To check how many runs you should do for each config
    `gen_config.py --list`
                                 """)

# Weird hack to allow --list with no other args
# Returns an Action that calls the function, then exits
def OverrideArg(func):
    class Override(argparse.Action):
        def __call__(self, parser, namespace, values, option_string):
            func()
            parser.exit() # exits the program with no more arg parsing and checking
    return Override


# This overrides normal arg parsing, prints confs, and exits
parser.add_argument("-l", "--list", nargs=0, action=OverrideArg(listConfs),  help="list number of configs")

parser.add_argument("config_id", help="which config to run")
parser.add_argument("n",   help="start the nth run for config_id", type=int)
parser.add_argument("-o", "--outfile",  help="path to write config file out to", required=True)
args = parser.parse_args()


# Will error out if goes wrong
conf = Config(args.config_id)



# Loaded template file
#print("\n=====\n" +template_str + "\n=======\n")#DEBUG


#class VarDict(dict):
#    """We want to override the default dict to make sure all variables are used"""
#    def __init__(self, varsObj):
#        self.update(**varsObj)
#        self.varsUsed = { k:0 for k in varsObj.keys()}
#
#    def __getitem__(self, key):
#        print(f"Accessed key {key}")
#        self.varsUsed[key] += 1
#        return super().__getitem__(key);
#
#v = VarDict(conf["_vars"])


#print(conf.genConf(args.n))

print(f"Writing to {args.outfile}")
try:
    with open(args.outfile, "w") as out:
        out.write(conf.genConf(args.n))
except IOError as e:
    err_exit(f"I/O error: {e}")
except Exception as e: #handle other exceptions such as attribute errors
    err_exit("Unexpected error:", e)

print(f"BAKE-STEP|GEN_CONFIG|SUCCESS| wrote conf '{args.config_id} {args.n}' to {args.outfile}")
