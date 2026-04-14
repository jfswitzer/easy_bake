#!/bin/bash

SESSION_NAME="my_task"
TARGET_DIR="/home/baking/coremark"
COMMAND="./run_litmus.sh"

# 1. Create a new session in the background (-d)
# 2. Start it in the specific directory (-c)
# 3. Give the session a name (-s)
# 4. Pass the command to run
tmux new-session -d -s "$SESSION_NAME" -c "$TARGET_DIR" "$COMMAND"

echo "Tmux session '$SESSION_NAME' has been launched in the background."
