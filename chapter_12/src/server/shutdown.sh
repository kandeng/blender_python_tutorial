#!/bin/bash   #isn't a simple comment 
echo 
echo "[INFO] shutdown.sh is shuting down the Blender AI agent system."
echo 

PYTHONPATH="${PYTHONPATH}:${PWD}"
export PYTHONPATH 

echo 
echo 
echo "=========================================================================================="
echo "    [1] Shut down min_io file storage, then wait for 5 seconds."
echo 

sudo systemctl stop minio
sleep 5


echo 
echo 
echo "=========================================================================================="
echo "    [2] Shut down postgre database, then wait for 5 seconds."
echo 

sudo systemctl stop postgresql
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
echo "    [4] Shut down fastapi web server, then wait for 5 seconds."
echo 

sudo systemctl stop fastapi-webserver
sleep 5


echo 
echo 
echo "=========================================================================================="
echo "    [5] Shut down langchain agents"
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