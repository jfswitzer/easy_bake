Scripts to be run on the pi

`gen_config.py` generated an updated tryboot.txt, based on the passed in config-id and run-number.
For example, if we defined a config "


`tryboot_template.txt` is a tryboot file with variables stubbed out

The `step_XXX.sh` files are simplified commands that should output 
    BAKE-STEP|CHECKLOGIN|SUCCESS|some long output message
They will be called via serial, and their responses parsed
