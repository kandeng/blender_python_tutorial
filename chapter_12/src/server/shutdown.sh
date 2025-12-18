#!/bin/bash   #isn't a simple comment 
echo 
echo "[INFO] shutdown.sh is shuting down the Blender AI agent system."

echo
echo "[INFO] Stop rabbitmq-server to clean up the environment. Then wait for 5 seconds ..."
sudo systemctl stop rabbitmq-server
sleep 5

PYTHONPATH="${PYTHONPATH}:${PWD}"
export PYTHONPATH 

# Reference: Is there a way to kill uvicorn cleanly?
# https://stackoverflow.com/questions/60424390/is-there-a-way-to-kill-uvicorn-cleanly
SERVER_PID="$(pgrep -f 'fastapi_engine')"

echo
echo "[INFO] Terminate fastapi_engine: " 
echo $(ps -p $SERVER_PID -f -o pid -o command | tail -n +2)

if [[ -n "$SERVER_PID" ]]
then
    # PGID="$(ps --no-headers -p $PID -o pgid)"
    PGID="$(ps -p $SERVER_PID -o pgid | tail -n +2)"
    echo "    PGID: $PGID, PID: $SERVER_PID"
    echo 
    # kill -SIGINT -- -${PGID// /}
    kill -SIGKILL -- ${SERVER_PID// /}
fi


AGENT_PID="$(pgrep -f 'orchestrator_agent')"

echo
echo "[INFO] Terminate orchestrator_agent: " 
echo $(ps -p $AGENT_PID -f -o pid -o command | tail -n +2)

if [[ -n "$AGENT_PID" ]]
then
    # PGID="$(ps --no-headers -p $PID -o pgid)"
    PGID="$(ps -p $AGENT_PID -o pgid | tail -n +2)"
    echo "    PGID: $PGID, PID: $AGENT_PID"
    echo 
    # kill -SIGINT -- -${PGID// /}
    kill -SIGKILL -- ${AGENT_PID// /}
fi