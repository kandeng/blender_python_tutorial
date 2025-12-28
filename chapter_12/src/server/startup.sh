#!/usr/bin/bash  #isn't a simple comment 
echo
echo "[INFO] startup.sh is starting up the Blender AI Agent server."
echo 

PYTHONPATH="${PYTHONPATH}:${PWD}"
export PYTHONPATH 

mkdir -p logs

echo 
echo 
echo "=========================================================================================="
echo "    [1] Start up min_io file storage, then wait for 5 seconds."
echo 

sudo systemctl start minio
sleep 5


echo 
echo 
echo "=========================================================================================="
echo "    [2] Start up postgre database, then wait for 5 seconds."
echo 

sudo systemctl start postgresql
sleep 5


echo 
echo 
echo "=========================================================================================="
echo "    [3] Start up fastapi web server, then wait for 5 seconds."
echo
echo " nohup python3 fastapi_server/fastapi_engine.py > logs/fastapi_engine_log.txt"
cd /home/robot/aiBlender/aiBlender_20251218/server
nohup python3 fastapi_server/fastapi_engine.py > logs/fastapi_engine_log.txt 2>&1 &
sleep 5

echo 
echo 
echo "=========================================================================================="
echo "    [4] Start up rabbitmq message queue service, then wait for 5 seconds."
echo 

sudo systemctl start rabbitmq-server
sleep 5


echo 
echo 
echo "=========================================================================================="
echo "    [5] Start up langchain agents"
echo

echo " nohup python3 langchain_agent/orchestrator_agent.py > logs/orchestrator_agent_log.txt"
cd /home/robot/aiBlender/aiBlender_20251218/server
nohup python3 langchain_agent/orchestrator_agent.py > logs/orchestrator_agent_log.txt 2>&1 &


echo 
echo 
echo "=========================================================================================="
echo 
echo 
echo "[INFO] startup.sh is completed."
