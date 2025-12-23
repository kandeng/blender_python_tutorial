#!/bin/bash   #isn't a simple comment 
echo 
echo "[INFO] shutdown.sh is shuting down the Blender AI agent system."
echo 

PYTHONPATH="${PYTHONPATH}:${PWD}"
export PYTHONPATH 


echo 
echo 
echo "=========================================================================================="
echo "    [1] Shut down chroma vector database, then wait for 5 seconds."
echo 

cd /home/robot/aiBlender/aiBlender_20251218/server
CHROMA_PID=$(cat ./logs/chroma.pid)
kill $CHROMA_PID
sleep 5

# Verify shutdown (curl will fail)
curl http://localhost:5566/api/v2/heartbeat 2>&1
echo "[INFO] Expect to see the error message: 'Failed to connect to ...'"
echo 

# Clean up pid file (optional)
rm ./logs/chroma.pid 



echo 
echo 
echo "=========================================================================================="
echo "    [2] Shut down fastapi web server, then wait for 5 seconds."
echo 

# Reference: Is there a way to kill uvicorn cleanly?
# https://stackoverflow.com/questions/60424390/is-there-a-way-to-kill-uvicorn-cleanly
SERVER_PID="$(pgrep -f 'fastapi_engine')"
echo $(ps -p $SERVER_PID -f -o pid -o command | tail -n +2)

if [[ -n "$SERVER_PID" ]]
then
    # PGID="$(ps --no-headers -p $PID -o pgid)"
    PGID="$(ps -p $SERVER_PID -o pgid | tail -n +2)"
    echo "    PGID: $PGID, PID: $SERVER_PID"
    
    # kill -SIGINT -- -${PGID// /}
    kill -SIGKILL -- ${SERVER_PID// /}
fi

sleep 5

echo 
echo 
echo "=========================================================================================="
echo "    [3] Shut down rabbitmq message queue service, then wait for 5 seconds."
echo 

sudo systemctl stop rabbitmq-server
sleep 5


echo 
echo 
echo "=========================================================================================="
echo "    [4] Shut down langchain agents"
echo 

AGENT_PID="$(pgrep -f 'orchestrator_agent')"
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

echo 
echo 
echo "=========================================================================================="
echo 
echo 
echo "[INFO] shutdown.sh is completed."