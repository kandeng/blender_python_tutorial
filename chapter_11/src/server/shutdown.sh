#!/bin/bash   #isn't a simple comment 
echo 
echo "shutdown.sh is shuting down the Blender AI agent ... "

PYTHONPATH="${PYTHONPATH}:${PWD}"
export PYTHONPATH 


# Reference: Is there a way to kill uvicorn cleanly?
# https://stackoverflow.com/questions/60424390/is-there-a-way-to-kill-uvicorn-cleanly
SERVER_PID="$(pgrep -f 'blender_agent_server')"

echo
echo "Terminate: " 
echo $(ps -p $SERVER_PID -f -o pid -o command | tail -n +2)

if [[ -n "$SERVER_PID" ]]
then
    # PGID="$(ps --no-headers -p $PID -o pgid)"
    PGID="$(ps -p $SERVER_PID -o pgid | tail -n +2)"
    echo " PGID: $PGID, PID: $SERVER_PID"
    echo 
    # kill -SIGINT -- -${PGID// /}
    kill -SIGKILL -- ${SERVER_PID// /}
fi